from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.db.session import get_db
from app.api.v1.endpoints.deps import get_current_user
from app.models.user import User
from app.rag.schemas import KnowledgeSourceCreate, KnowledgeSourceResponse, RAGQueryRequest, RAGQueryResponse
from app.rag.models import KnowledgeSource
from app.rag.service import RAGService, RAGGenerator

router = APIRouter()

@router.post("/sources", response_model=KnowledgeSourceResponse)
def create_knowledge_source(source: KnowledgeSourceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return RAGService.create_source(db, current_user, source)

@router.get("/sources", response_model=List[KnowledgeSourceResponse])
def list_knowledge_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(KnowledgeSource).filter(KnowledgeSource.company_id == current_user.company_id).all()

@router.get("/sources/{source_id}", response_model=KnowledgeSourceResponse)
def get_knowledge_source(source_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    source = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id, KnowledgeSource.company_id == current_user.company_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

@router.delete("/sources/{source_id}")
def delete_knowledge_source(source_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    source = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id, KnowledgeSource.company_id == current_user.company_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"status": "deleted"}

@router.post("/sources/{source_id}/ingest")
def ingest_document(source_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if file.content_type not in ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/markdown"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    try:
        content = file.file.read()
        doc = RAGService.ingest_document(db, current_user, source_id, content, file.filename, file.content_type)
        return {"document_id": doc.id, "status": doc.status}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/query", response_model=RAGQueryResponse)
def query_knowledge(request: RAGQueryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    generator = RAGGenerator(db, current_user)
    return generator.answer_query(request)
