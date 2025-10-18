import os
# Disable ChromaDB telemetry before importing
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from config import Config


class VectorStoreService:
    """Service for managing vector embeddings with ChromaDB"""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or Config.CHROMA_PERSIST_DIR
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=self.persist_directory,
            anonymized_telemetry=False
        ))
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize collections
        self._init_collections()
    
    def _init_collections(self):
        """Initialize ChromaDB collections"""
        # Collection for job descriptions
        self.job_descriptions = self.client.get_or_create_collection(
            name="job_descriptions",
            metadata={"description": "Job description embeddings"}
        )
        
        # Collection for evaluation rubrics
        self.rubrics = self.client.get_or_create_collection(
            name="rubrics",
            metadata={"description": "Evaluation rubric embeddings"}
        )
        
        # Collection for case studies
        self.case_studies = self.client.get_or_create_collection(
            name="case_studies",
            metadata={"description": "Case study embeddings"}
        )
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to a collection
        
        Args:
            collection_name: Name of the collection
            documents: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
            
        Returns:
            True if successful
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            # Generate IDs if not provided
            if ids is None:
                ids = [f"{collection_name}_{i}" for i in range(len(documents))]
            
            # Add documents
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return True
        except Exception as e:
            print(f"Error adding documents to {collection_name}: {str(e)}")
            return False
    
    def query_similar(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 3
    ) -> List[Dict]:
        """
        Query similar documents from a collection
        
        Args:
            collection_name: Name of the collection
            query_text: Query text
            n_results: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            # Query the collection
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'document': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    }
                    formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            print(f"Error querying {collection_name}: {str(e)}")
            return []
    
    def seed_initial_data(self):
        """Seed vector store with initial reference documents"""
        
        # General Job Evaluation Context (No specific job descriptions)
        job_evaluation_context = """
        General Job Evaluation Guidelines
        
        This system evaluates candidates for ANY job position by analyzing:
        1. Field Relevance: Does the candidate's background match the job field?
        2. Skill Transferability: Can existing skills be applied to the new role?
        3. Experience Level: Years and depth of relevant experience
        4. Technical Competency: Required technical skills and knowledge
        5. Cultural Fit: Communication, teamwork, and adaptability
        
        Evaluation Principles:
        - Tech/Engineering roles require technical skills and experience
        - Service/Hospitality roles require customer service and communication skills
        - Management roles require leadership and organizational skills
        - Creative roles require portfolio and artistic skills
        - Sales roles require persuasion and relationship-building skills
        
        Field Mismatch Detection:
        - Software Engineer applying for Barista = Field Mismatch
        - Data Scientist applying for Janitor = Field Mismatch  
        - Backend Developer applying for Frontend Developer = Same Field
        - Marketing Manager applying for Sales Manager = Related Field
        
        The system should be strict about field relevance while being fair about skill transferability within related fields.
        """
        
        # Job descriptions removed - using general evaluation guidelines instead
        
        # Add general job evaluation context to vector store
        self.add_documents(
            "job_evaluation_context",
            [job_evaluation_context],
            [{"type": "job_evaluation_guidelines"}],
            ["job_eval_context"]
        )
        
        # CV Evaluation Rubric
        cv_evaluation_guidelines = """
        CV Match Evaluation (1–5 scale per parameter)

        Technical Skills Match (Weight: 40%):
        Alignment with job requirements (backend, databases, APIs, cloud, AI/LLM).
        - 1 = Irrelevant skills
        - 2 = Few overlaps
        - 3 = Partial match
        - 4 = Strong match
        - 5 = Excellent match + AI/LLM exposure

        Experience Level (Weight: 25%):
        Years of experience and project complexity.
        - 1 = <1 yr / trivial projects
        - 2 = 1–2 yrs
        - 3 = 2–3 yrs with mid-scale projects
        - 4 = 3–4 yrs solid track record
        - 5 = 5+ yrs / high-impact projects

        Relevant Achievements (Weight: 20%):
        Impact of past work (scaling, performance, adoption).
        - 1 = No clear achievements
        - 2 = Minimal improvements
        - 3 = Some measurable outcomes
        - 4 = Significant contributions
        - 5 = Major measurable impact

        Cultural / Collaboration Fit (Weight: 15%):
        Communication, learning mindset, teamwork/leadership.
        - 1 = Not demonstrated
        - 2 = Minimal
        - 3 = Average
        - 4 = Good
        - 5 = Excellent and well-demonstrated

        CV Match Rate: Weighted Average (1–5) → Convert to 0–1 decimal (×0.2)
        """

        # Project Evaluation Rubric
        project_evaluation_guidelines = """
        Project Deliverable Evaluation (1–5 scale per parameter)

        Correctness (Prompt & Chaining) (Weight: 30%):
        Implements prompt design, LLM chaining, RAG context injection.
        - 1 = Not implemented
        - 2 = Minimal attempt
        - 3 = Works partially
        - 4 = Works correctly
        - 5 = Fully correct + thoughtful

        Code Quality & Structure (Weight: 25%):
        Clean, modular, reusable, tested.
        - 1 = Poor
        - 2 = Some structure
        - 3 = Decent modularity
        - 4 = Good structure + some tests
        - 5 = Excellent quality + strong tests

        Resilience & Error Handling (Weight: 20%):
        Handles long jobs, retries, randomness, API failures.
        - 1 = Missing
        - 2 = Minimal
        - 3 = Partial handling
        - 4 = Solid handling
        - 5 = Robust, production-ready

        Documentation & Explanation (Weight: 15%):
        README clarity, setup instructions, trade-off explanations.
        - 1 = Missing
        - 2 = Minimal
        - 3 = Adequate
        - 4 = Clear
        - 5 = Excellent + insightful

        Creativity / Bonus (Weight: 10%):
        Extra features beyond requirements.
        - 1 = None
        - 2 = Very basic
        - 3 = Useful extras
        - 4 = Strong enhancements
        - 5 = Outstanding creativity

        Project Score: Weighted Average (1–5)
        """
        
        # Case Study Brief
        case_study = """
        Backend Developer Case Study: CV and Project Evaluation System
        
        Task: Build a backend service that evaluates CVs and project reports using LLM and RAG.
        
        Requirements:
        1. File Upload API endpoint accepting CV and project report PDFs
        2. Evaluation API endpoint that processes files asynchronously
        3. Result retrieval endpoint for checking job status and results
        4. Integration with vector database for RAG
        5. LLM-powered evaluation with structured scoring
        6. Proper error handling and retry mechanisms
        7. Clean, production-ready code
        8. Comprehensive documentation
        
        Technical Stack:
        - Flask/FastAPI for API
        - Celery + Redis for async processing
        - ChromaDB/Qdrant for vector storage
        - OpenAI/Anthropic for LLM
        - SQLite/PostgreSQL for job tracking
        
        Deliverables:
        - Working API with all endpoints
        - Async job processing system
        - Vector store integration
        - LLM evaluation pipeline
        - Documentation (README + API docs)
        """
        
        # Add evaluation guidelines to vector store
        self.add_documents(
            "evaluation_guidelines",
            [cv_evaluation_guidelines, project_evaluation_guidelines],
            [
                {"type": "cv_evaluation", "category": "candidate_evaluation"},
                {"type": "project_evaluation", "category": "project_evaluation"}
            ],
            ["cv_evaluation_guidelines", "project_evaluation_guidelines"]
        )
        
        self.add_documents(
            "case_studies",
            [case_study],
            [{"type": "case_study", "title": "CV and Project Evaluation System"}],
            ["backend_dev_case_study"]
        )
        
        print("✅ Vector store seeded with initial data")
    
    def get_job_description_context(self, job_title: str) -> str:
        """Get relevant job description context"""
        results = self.query_similar("job_descriptions", job_title, n_results=1)
        return results[0]['document'] if results else ""
    
    def get_cv_rubric_context(self) -> str:
        """Get CV evaluation rubric"""
        results = self.query_similar("rubrics", "cv evaluation criteria", n_results=1)
        return results[0]['document'] if results else ""
    
    def get_project_rubric_context(self) -> str:
        """Get project evaluation rubric"""
        results = self.query_similar("rubrics", "project evaluation criteria", n_results=1)
        return results[0]['document'] if results else ""
    
    def get_case_study_context(self) -> str:
        """Get case study context"""
        results = self.query_similar("case_studies", "backend developer case study", n_results=1)
        return results[0]['document'] if results else ""

