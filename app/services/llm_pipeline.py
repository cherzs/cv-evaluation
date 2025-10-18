import json
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config
from app.services.vector_store import VectorStoreService
from app.services.gemini_client import GeminiClient
from app.utils.pdf_parser import PDFParser


class LLMPipeline:
    """Service for LLM-powered evaluation pipeline using Google Gemini"""
    
    def __init__(self):
        # Initialize Gemini client
        self.llm_client = GeminiClient()
        
        # Initialize vector store
        self.vector_store = VectorStoreService()
        
        # Initialize PDF parser
        self.pdf_parser = PDFParser()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call Gemini LLM with retry logic
        
        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            
        Returns:
            LLM response as string
        """
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            response = self.llm_client.chat(messages)
            return response
                
        except Exception as e:
            print(f"Gemini LLM API error: {str(e)}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks
        
        Args:
            response: LLM response text
            
        Returns:
            Parsed JSON dictionary
        """
        try:
            # Remove markdown code blocks if present
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            # Try normal parsing first
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {str(e)}")
            print(f"Attempting to fix control characters...")
            
            try:
                # Try with strict=False to handle control characters
                return json.loads(response, strict=False)
            except:
                # Last resort: manually escape common control characters in string values
                import re
                # Fix newlines, tabs, etc in string values
                response = response.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                return json.loads(response)
        except Exception as e:
            print(f"Failed to parse JSON after all attempts")
            print(f"Response: {response[:500]}...")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
    
    def evaluate_cv(
        self,
        cv_path: str,
        job_title: str
    ) -> Dict[str, Any]:
        """
        Evaluate CV against job requirements
        
        Args:
            cv_path: Path to CV PDF
            job_title: Job title for evaluation
            
        Returns:
            CV evaluation results
        """
        # Extract CV text
        cv_text = self.pdf_parser.extract_text(cv_path)
        
        # Get relevant context from vector store
        job_desc_context = self.vector_store.get_job_description_context(job_title)
        cv_rubric_context = self.vector_store.get_cv_rubric_context()
        
        # Construct system prompt
        system_prompt = """You are an expert recruiter evaluating candidate CVs with ZERO TOLERANCE for field mismatch.
        
        MOST IMPORTANT RULE: If the candidate's career field is DIFFERENT from the job field, ALL scores MUST be 1.
        - Tech/Engineering ≠ Hospitality/Service
        - Data Science ≠ Barista
        - Software ≠ Customer Service
        
        Do NOT give credit for "transferable skills" or "general experience" if the field is wrong.
        Experience as a software engineer does NOT count as experience for a barista position.
        
        Always respond with valid JSON only, no additional text."""
        
        # Construct user prompt
        user_prompt = f"""
Evaluate the following CV for the position: {job_title}

JOB DESCRIPTION:
{job_desc_context}

EVALUATION RUBRIC:
{cv_rubric_context}

CANDIDATE CV:
{cv_text[:4000]}

CRITICAL EVALUATION RULES - READ CAREFULLY:
1. FIELD MISMATCH CHECK: Is the candidate's career field the SAME as the job? 
   - Tech/Engineering vs Hospitality/Service = DIFFERENT
   - Data Science vs Barista = DIFFERENT
   - Backend Developer vs Frontend Developer = SAME (both tech)
   
2. IF FIELD MISMATCH: ALL scores MUST be 1, including:
   - technical_match = 1 (no relevant skills)
   - experience_score = 1 (experience in WRONG field doesn't count!)
   - achievements_score = 1 (achievements in WRONG field don't count!)
   - cultural_fit_score = 1 (assume no fit if wrong field)
   
3. "Experience" means experience in THIS SPECIFIC FIELD, not just any work experience.
   Example: 5 years as software engineer ≠ experience for barista position.
   
4. Be BRUTALLY HONEST. If it's wrong field, don't give sympathy points.

5. Use WEIGHTED SCORING: Technical (40%), Experience (25%), Achievements (20%), Cultural Fit (15%)

Please evaluate the candidate and respond with the following JSON structure:
{{
    "technical_match": <integer 1-5. MUST be 1 if field mismatch>,
    "experience_score": <integer 1-5. MUST be 1 if experience is in different field>,
    "achievements_score": <integer 1-5. MUST be 1 if achievements are in different field>,
    "cultural_fit_score": <integer 1-5. MUST be 1 if field mismatch>,
    "cv_match_rate": <CALCULATED: (technical*0.4 + experience*0.25 + achievements*0.2 + cultural*0.15) / 5>,
    "cv_feedback": "<detailed feedback - START with 'FIELD MISMATCH:' if wrong field>"
}}

CALCULATION EXAMPLES:
Example 1 - Matched field (Backend Dev applying for Backend Dev):
- technical=4, experience=3, achievements=4, cultural=3
- cv_match_rate = (4*0.4 + 3*0.25 + 4*0.2 + 3*0.15) / 5 = 3.4 / 5 = 0.68

Example 2 - Mismatched field (Software Engineer applying for Barista):
- technical=1, experience=1, achievements=1, cultural=1 (ALL MUST BE 1!)
- cv_match_rate = (1*0.4 + 1*0.25 + 1*0.2 + 1*0.15) / 5 = 1.0 / 5 = 0.20

Be STRICT and HONEST in your evaluation.
"""
        
        # Call LLM
        response = self._call_llm(system_prompt, user_prompt)
        
        # Parse response
        evaluation = self._parse_json_response(response)
        
        return evaluation
    
    def evaluate_project(
        self,
        project_path: str,
        job_title: str = "Backend Developer"
    ) -> Dict[str, Any]:
        """
        Evaluate project report against case study requirements
        
        Args:
            project_path: Path to project report PDF
            job_title: Job title to check project relevance
            
        Returns:
            Project evaluation results
        """
        # Extract project text
        project_text = self.pdf_parser.extract_text(project_path)
        
        # Get relevant context from vector store
        case_study_context = self.vector_store.get_case_study_context()
        project_rubric_context = self.vector_store.get_project_rubric_context()
        
        # Construct system prompt
        system_prompt = """You are a senior technical interviewer evaluating project submissions.
        
        CRITICAL: Check if the project is RELEVANT to the job position.
        - If applying for NON-TECH roles (Janitor, Barista, Receptionist, etc.) and project is TECH/SOFTWARE project, ALL scores MUST be 1.
        - A backend development project is NOT relevant for Janitor, Barista, or other non-tech roles.
        
        Use WEIGHTED SCORING: Correctness (30%), Code Quality (25%), Resilience (20%), Documentation (15%), Creativity (10%)
        Always respond with valid JSON only, no additional text."""
        
        # Construct user prompt
        user_prompt = f"""
JOB POSITION: {job_title}

Evaluate the following project submission for the case study.

IMPORTANT: Is this project RELEVANT to the job position?
- If job is NON-TECH (Janitor, Barista, Receptionist) and project is SOFTWARE/TECH → ALL scores MUST be 1
- If job is TECH (Backend Developer, Data Analyst) and project is SOFTWARE → Evaluate normally

CASE STUDY REQUIREMENTS:
{case_study_context}

EVALUATION RUBRIC:
{project_rubric_context}

PROJECT REPORT/DOCUMENTATION:
{project_text[:4000]}

EVALUATION CRITERIA WITH WEIGHTS:
1. Correctness (30%): Prompt chaining, RAG implementation, error handling, requirements coverage
2. Code Quality (25%): Modular, testable, clean code, best practices
3. Resilience (20%): Retry mechanisms, long job handling, API failure recovery
4. Documentation (15%): README quality, API docs, setup instructions, trade-offs
5. Creativity (10%): Bonus features (auth, dashboard, deployment), innovative solutions

CRITICAL RULE FOR PROJECT RELEVANCE:
- If job is NON-TECH (Janitor, Barista, Receptionist, Security Guard, Cleaner, Driver, etc.)
  AND project is SOFTWARE/TECH project (backend system, API, web app, mobile app, etc.)
  → ALL SCORES MUST BE 1 (project not relevant to job)

Please evaluate the project and respond with the following JSON structure:
{{
    "correctness_score": <integer 1-5. MUST be 1 if project not relevant to job>,
    "code_quality_score": <integer 1-5. MUST be 1 if project not relevant to job>,
    "resilience_score": <integer 1-5. MUST be 1 if project not relevant to job>,
    "documentation_score": <integer 1-5. MUST be 1 if project not relevant to job>,
    "creativity_score": <integer 1-5. MUST be 1 if project not relevant to job>,
    "project_score": <CALCULATED: (correctness*0.3 + code_quality*0.25 + resilience*0.2 + documentation*0.15 + creativity*0.1)>,
    "project_feedback": "<detailed feedback - START with 'PROJECT NOT RELEVANT:' if project is for different field>"
}}

CALCULATION EXAMPLES:
Example 1 - Relevant project (Backend Developer applying with Backend project):
- correctness=4, code_quality=4, resilience=3, documentation=4, creativity=3
- project_score = 4*0.3 + 4*0.25 + 3*0.2 + 4*0.15 + 3*0.1 = 3.7

Example 2 - Irrelevant project (Janitor applying with Backend project):
- correctness=1, code_quality=1, resilience=1, documentation=1, creativity=1 (ALL MUST BE 1!)
- project_score = 1*0.3 + 1*0.25 + 1*0.2 + 1*0.15 + 1*0.1 = 1.0

Be thorough and constructive in your evaluation.
"""
        
        # Call LLM
        response = self._call_llm(system_prompt, user_prompt)
        
        # Parse response
        evaluation = self._parse_json_response(response)
        
        return evaluation
    
    def generate_final_summary(
        self,
        cv_evaluation: Dict[str, Any],
        project_evaluation: Dict[str, Any],
        job_title: str
    ) -> Dict[str, Any]:
        """
        Generate final summary and recommendation
        
        Args:
            cv_evaluation: CV evaluation results
            project_evaluation: Project evaluation results
            job_title: Job title
            
        Returns:
            Final evaluation with summary
        """
        # Construct system prompt
        system_prompt = """You are a hiring manager making final candidate decisions.
        Synthesize CV and project evaluations into a clear recommendation.
        If CV match rate is below 0.3, the candidate is from a WRONG FIELD and MUST be "Not Recommended".
        Always respond with valid JSON only, no additional text."""
        
        # Construct user prompt
        user_prompt = f"""
Based on the following evaluations, provide a final summary and hiring recommendation.

POSITION: {job_title}

CV EVALUATION (Weighted: Technical 40%, Experience 25%, Achievements 20%, Cultural 15%):
- CV Match Rate: {cv_evaluation.get('cv_match_rate', 0):.2f}
- Technical Skills Match (40%): {cv_evaluation.get('technical_match', 0)}/5
- Experience Level (25%): {cv_evaluation.get('experience_score', 0)}/5
- Relevant Achievements (20%): {cv_evaluation.get('achievements_score', 0)}/5
- Cultural/Collaboration Fit (15%): {cv_evaluation.get('cultural_fit_score', 0)}/5
- Feedback: {cv_evaluation.get('cv_feedback', 'N/A')}

PROJECT EVALUATION (Weighted: Correctness 30%, Code Quality 25%, Resilience 20%, Documentation 15%, Creativity 10%):
- Project Score: {project_evaluation.get('project_score', 0):.2f}/5
- Correctness (Prompt & Chaining) (30%): {project_evaluation.get('correctness_score', 0)}/5
- Code Quality & Structure (25%): {project_evaluation.get('code_quality_score', 0)}/5
- Resilience & Error Handling (20%): {project_evaluation.get('resilience_score', 0)}/5
- Documentation & Explanation (15%): {project_evaluation.get('documentation_score', 0)}/5
- Creativity/Bonus (10%): {project_evaluation.get('creativity_score', 0)}/5
- Feedback: {project_evaluation.get('project_feedback', 'N/A')}

SCORING RUBRIC CONTEXT:
This is a Case Study Evaluation for a Backend Developer position. The candidate submitted a CV and project report for evaluation against backend development requirements including AI/LLM integration, prompt chaining, RAG implementation, and production-ready code.

OVERALL SUMMARY REQUIREMENTS:
Provide 3-5 sentences summarizing:
1. The candidate's key strengths (skills, performance, problem-solving ability)
2. Identified gaps or improvement areas
3. Recommendations for next steps (e.g., mentorship, deployment readiness, or role fit)

RECOMMENDATION RULES:
- If CV Match Rate <= 0.25: "Not Recommended" (wrong field)
- If CV Match Rate < 0.40: "Not Recommended" (major mismatch)
- If CV Match Rate < 0.50: "Maybe" at best
- If CV Match Rate >= 0.60 and Project Score >= 3.0: "Recommended"
- If CV Match Rate >= 0.75 and Project Score >= 4.0: "Highly Recommended"

Please provide a final evaluation with the following JSON structure:
{{
    "final_summary": "<3-5 sentence summary focusing on key strengths, gaps, and next steps>",
    "recommendation": "<one of: 'Highly Recommended', 'Recommended', 'Maybe', 'Not Recommended'>",
    "overall_score": <float between 0 and 5, weighted average>
}}

Be STRICT and HONEST in your recommendation.
"""
        
        # Call LLM
        response = self._call_llm(system_prompt, user_prompt)
        
        # Parse response
        summary = self._parse_json_response(response)
        
        # Combine all results
        final_result = {
            "cv_evaluation": cv_evaluation,
            "project_evaluation": project_evaluation,
            **summary
        }
        
        return final_result
    
    def run_full_evaluation(
        self,
        cv_path: str,
        project_path: str,
        job_title: str
    ) -> Dict[str, Any]:
        """
        Run complete evaluation pipeline
        
        Args:
            cv_path: Path to CV PDF
            project_path: Path to project report PDF
            job_title: Job title for evaluation
            
        Returns:
            Complete evaluation results
        """
        try:
            # Stage 1: CV Evaluation
            cv_evaluation = self.evaluate_cv(cv_path, job_title)
            
            # Stage 2: Project Evaluation (with job title for relevance check)
            project_evaluation = self.evaluate_project(project_path, job_title)
            
            # Stage 3: Final Summary
            final_result = self.generate_final_summary(
                cv_evaluation,
                project_evaluation,
                job_title
            )
            
            return final_result
            
        except Exception as e:
            print(f"Evaluation pipeline error: {str(e)}")
            raise
