from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class UploadResponse(BaseModel):
    """Response schema for file upload"""
    cv_id: str
    report_id: str
    message: str = "Files uploaded successfully"


class EvaluateRequest(BaseModel):
    """Request schema for evaluation"""
    job_title: str = Field(..., min_length=1, max_length=255)
    cv_id: str = Field(..., min_length=1)
    report_id: str = Field(..., min_length=1)


class EvaluateResponse(BaseModel):
    """Response schema for evaluation request"""
    job_id: str
    status: str = "queued"
    message: str = "Evaluation job queued successfully"


class JobStatus(BaseModel):
    """Job status response schema"""
    id: str
    job_title: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CVEvaluation(BaseModel):
    """CV evaluation result schema"""
    cv_match_rate: float = Field(..., ge=0, le=1)
    technical_match: int = Field(..., ge=1, le=5)
    experience_score: int = Field(..., ge=1, le=5)
    achievements_score: int = Field(..., ge=1, le=5)
    cultural_fit_score: int = Field(..., ge=1, le=5)
    cv_feedback: str


class ProjectEvaluation(BaseModel):
    """Project evaluation result schema"""
    project_score: float = Field(..., ge=0, le=5)
    correctness_score: int = Field(..., ge=1, le=5)
    code_quality_score: int = Field(..., ge=1, le=5)
    resilience_score: int = Field(..., ge=1, le=5)
    documentation_score: int = Field(..., ge=1, le=5)
    project_feedback: str


class FinalEvaluation(BaseModel):
    """Final evaluation result schema"""
    cv_evaluation: CVEvaluation
    project_evaluation: ProjectEvaluation
    final_summary: str
    recommendation: str  # "Highly Recommended", "Recommended", "Maybe", "Not Recommended"
    overall_score: float = Field(..., ge=0, le=5)


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    message: str
    status_code: int

