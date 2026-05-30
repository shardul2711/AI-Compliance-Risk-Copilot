from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.db.session import get_db
from backend.app.models.models import AuditLog, User
from backend.app.schemas.schemas import AuditLogResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    document_id: Optional[int] = Query(None, description="Filter logs by document ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only Admins should see the overall audit logs. Analysts can only query audit logs of their own documents
    query = db.query(AuditLog)
    
    if document_id is not None:
        query = query.filter(AuditLog.document_id == document_id)
        
    if current_user.role != "Admin":
        # Filter for only documents that belong to this analyst
        # We perform a join with Document to check the user_id
        from backend.app.models.models import Document
        query = query.join(Document, AuditLog.document_id == Document.id).filter(Document.user_id == current_user.id)
        
    return query.order_by(AuditLog.created_at.desc()).all()
