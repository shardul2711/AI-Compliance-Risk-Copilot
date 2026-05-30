from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import datetime
from backend.app.db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="Analyst")  # Admin, Analyst
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=True)  # Contract, NDA, Policy, Regulation, Vendor Agreement
    status = Column(String(20), default="Uploaded")  # Uploaded, Processing, Analyzed, Failed
    file_path = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    clauses = relationship("Clause", back_populates="document", cascade="all, delete-orphan")
    compliance_results = relationship("ComplianceResult", back_populates="document", cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", uselist=False, back_populates="document", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="document", cascade="all, delete-orphan")
    executive_report = relationship("ExecutiveReport", uselist=False, back_populates="document", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    document = relationship("Document", back_populates="chunks")

class Clause(Base):
    __tablename__ = "clauses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    clause_type = Column(String(50), nullable=False)  # Confidentiality, Data Privacy, Liability, etc.
    clause_text = Column(Text, nullable=False)
    risk_level = Column(String(20), default="Low")  # Low, Medium, High, Critical
    
    document = relationship("Document", back_populates="clauses")

class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    framework = Column(String(20), nullable=False)  # GDPR, HIPAA, SOC2, ISO27001, PCI-DSS
    requirement = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # Compliant, Non-Compliant, Partially-Compliant, Not-Applicable
    gap_description = Column(Text, nullable=True)
    
    document = relationship("Document", back_populates="compliance_results")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_level = Column(String(20), nullable=False)  # Low, Medium, High, Critical
    prediction_model = Column(String(50), default="XGBoost")
    
    document = relationship("Document", back_populates="risk_assessment")

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    recommendation = Column(Text, nullable=False)
    
    document = relationship("Document", back_populates="recommendations")

class ExecutiveReport(Base):
    __tablename__ = "executive_reports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=False)
    
    document = relationship("Document", back_populates="executive_report")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    agent_name = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    document = relationship("Document", back_populates="audit_logs")
