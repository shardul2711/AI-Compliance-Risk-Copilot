from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
import os
import shutil
import logging
from typing import List

from backend.app.db.session import get_db
from backend.app.models.models import Document, User, DocumentChunk, Clause, ComplianceResult, RiskAssessment, ExecutiveReport
from backend.app.schemas.schemas import (
    DocumentResponse, DocumentDetailResponse, RiskAssessmentResponse,
    ExecutiveReportResponse, ChatRequest, ChatResponse
)
from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.services.pdf_service import pdf_service
from backend.rag.vectorstore.qdrant_store import qdrant_store
from backend.rag.retriever.retriever import rag_retriever
from backend.langgraph.workflow import run_compliance_copilot_workflow

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

async def execute_analysis_pipeline(document_id: int, filename: str, file_path: str):
    """Background task to run PDF chunking + LangGraph analysis."""
    db = SessionLocal_helper()
    try:
        logger.info(f"Starting processing pipeline for doc {document_id}...")
        # Step 1: Extract, Clean, Chunk & Index in Qdrant
        success, msg = pdf_service.process_document(db, document_id)
        if not success:
            logger.error(f"Processing failed for document {document_id}: {msg}")
            return
            
        # Step 2: Retrieve full text from database chunks
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()
        
        full_text = "\n\n".join([c.chunk_text for c in chunks])
        
        # Step 3: Trigger LangGraph sequential workflow
        logger.info(f"Triggering LangGraph workflow for document {document_id}...")
        await run_compliance_copilot_workflow(
            document_id=document_id,
            filename=filename,
            document_text=full_text
        )
        logger.info(f"Analysis completed successfully for document {document_id}.")
        
    except Exception as e:
        logger.error(f"Error in background analysis task for document {document_id}: {e}")
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "Failed"
            db.commit()
    finally:
        db.close()

def SessionLocal_helper():
    from backend.app.db.session import SessionLocal
    return SessionLocal()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF documents are supported."
        )
        
    # Save file locally
    file_id = len(db.query(Document).all()) + 1 # simple incremental ID prefix for file safety
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not save uploaded file: {str(e)}"
        )
        
    # Create DB entry
    db_doc = Document(
        user_id=current_user.id,
        filename=file.filename,
        status="Uploaded",
        file_path=file_path
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    return db_doc


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Analysts and Admins see their own uploads, or we can make Admins see all.
    if current_user.role == "Admin":
        docs = db.query(Document).all()
    else:
        docs = db.query(Document).filter(Document.user_id == current_user.id).all()
        
    results = []
    for d in docs:
        results.append({
            "id": d.id,
            "user_id": d.user_id,
            "filename": d.filename,
            "document_type": d.document_type,
            "status": d.status,
            "uploaded_at": d.uploaded_at,
            "risk_score": d.risk_assessment.risk_score if d.risk_assessment else None,
            "risk_level": d.risk_assessment.risk_level if d.risk_assessment else None
        })
    return results


@router.get("/{id}", response_model=DocumentDetailResponse)
def get_document_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # Auth check
    if current_user.role != "Admin" and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document.")
        
    return doc


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_document(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # Auth check
    if current_user.role != "Admin" and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document.")
        
    # Delete local file
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.error(f"Failed to remove file {doc.file_path}: {e}")
            
    # Delete from Qdrant vector store
    qdrant_store.delete_document_chunks(id)
    
    # Delete database record (cascades will clean chunks, clauses, compliance, report, assessments)
    db.delete(doc)
    db.commit()
    
    return {"message": "Document and all associated analyses deleted successfully."}


@router.post("/{id}/analyze")
async def analyze_document(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # Auth check
    if current_user.role != "Admin" and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to analyze this document.")
        
    if doc.status == "Processing":
        return {"message": "Analysis is already in progress."}
        
    # Queue background pipeline tasks
    doc.status = "Processing"
    db.commit()
    
    background_tasks.add_task(execute_analysis_pipeline, id, doc.filename, doc.file_path)
    return {"message": "Analysis queued. Processing document text and invoking AI agents..."}


@router.post("/{id}/chat", response_model=ChatResponse)
async def chat_document(
    id: int,
    chat_req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # Auth check
    if current_user.role != "Admin" and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document.")
        
    if doc.status not in ["Processed", "Analyzed"]:
        raise HTTPException(
            status_code=400,
            detail="Document must be processed/analyzed before chatting."
        )
        
    response = await rag_retriever.generate_answer(document_id=id, query=chat_req.message)
    return response


@router.get("/{id}/risk", response_model=RiskAssessmentResponse)
def get_document_risk(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    if not doc.risk_assessment:
        raise HTTPException(
            status_code=400,
            detail="No risk assessment available. Please run analysis first."
        )
        
    return doc.risk_assessment


@router.get("/{id}/report", response_model=ExecutiveReportResponse)
def get_document_report(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    if not doc.executive_report:
        raise HTTPException(
            status_code=400,
            detail="No executive report available. Please run analysis first."
        )
        
    return doc.executive_report
