from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# Auth Schemas
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "Analyst"  # Admin, Analyst

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# Compliance & Clauses Schemas
class ClauseResponse(BaseModel):
    id: int
    clause_type: str
    clause_text: str
    risk_level: str

    class Config:
        from_attributes = True

class ComplianceResultResponse(BaseModel):
    id: int
    framework: str
    requirement: str
    status: str
    gap_description: Optional[str] = None

    class Config:
        from_attributes = True

class RiskAssessmentResponse(BaseModel):
    id: int
    risk_score: float
    risk_level: str
    prediction_model: str

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    id: int
    recommendation: str

    class Config:
        from_attributes = True

class ExecutiveReportResponse(BaseModel):
    id: int
    summary: str

    class Config:
        from_attributes = True

# Document Schemas
class DocumentResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    document_type: Optional[str] = None
    status: str
    uploaded_at: datetime
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentDetailResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    document_type: Optional[str] = None
    status: str
    uploaded_at: datetime
    
    clauses: List[ClauseResponse] = []
    compliance_results: List[ComplianceResultResponse] = []
    risk_assessment: Optional[RiskAssessmentResponse] = None
    recommendations: List[RecommendationResponse] = []
    executive_report: Optional[ExecutiveReportResponse] = None

    class Config:
        from_attributes = True

# Audit Log Schema
class AuditLogResponse(BaseModel):
    id: int
    document_id: Optional[int] = None
    agent_name: str
    action: str
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Schemas
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    retrieved_chunks: List[str] = []
