import uuid
import re
import math
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.models.user import User
from app.rag.models import KnowledgeSource, KnowledgeDocument, KnowledgeChunk
from app.rag.schemas import KnowledgeSourceCreate, RAGQueryRequest, RAGCitation, RAGQueryResponse
from app.ai.providers import get_provider

# PHASE 326 - EMBEDDING ABSTRACTION
class EmbeddingProvider:
    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

class MockEmbeddingProvider(EmbeddingProvider):
    def embed_text(self, text: str) -> List[float]:
        # Generate a deterministic mock vector based on length and first characters
        # for simple testing (len=128)
        base = sum(ord(c) for c in text[:10])
        vec = [(base + i) % 100 / 100.0 for i in range(128)]
        # Normalize
        norm = math.sqrt(sum(v*v for v in vec)) or 1
        return [v/norm for v in vec]

def get_embedding_provider() -> EmbeddingProvider:
    return MockEmbeddingProvider()

# PHASE 324 - DOCUMENT PROCESSING
class DocumentProcessor:
    @staticmethod
    def extract_text(file: UploadFile) -> str:
        # Mock basic extraction
        return "Simulated extracted text content from document."

# PHASE 325 - CHUNKING
class Chunker:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

# PHASE 327 - VECTOR STORAGE (Abstraction over PostgreSQL / ARRAY(Float))
class VectorStore:
    def __init__(self, db: Session):
        self.db = db

    def store_chunks(self, document_id: uuid.UUID, company_id: uuid.UUID, chunks: List[str], embeddings: List[List[float]]):
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            kc = KnowledgeChunk(
                document_id=document_id,
                company_id=company_id,
                chunk_index=i,
                content=chunk,
                embedding=emb
            )
            self.db.add(kc)
        self.db.commit()

# PHASE 328 & 329 & 330 - RETRIEVAL AND RERANKING
class Retriever:
    def __init__(self, db: Session, embedder: EmbeddingProvider):
        self.db = db
        self.embedder = embedder

    def search(self, company_id: uuid.UUID, query: str, top_k: int = 5, source_id: Optional[uuid.UUID] = None) -> List[KnowledgeChunk]:
        # Phase 329: Hybrid (mocking keyword + semantic by retrieving candidates)
        query_emb = self.embedder.embed_text(query)
        
        # Phase 334: Knowledge Access Control (Tenant scoped)
        query_filter = [KnowledgeChunk.company_id == company_id]
        if source_id:
            query_filter.append(KnowledgeChunk.document.has(source_id=source_id))
            
        candidates = self.db.query(KnowledgeChunk).filter(*query_filter).all()
        
        # Semantic + Keyword Reranking (Phase 330)
        scored = []
        for c in candidates:
            # Semantic dot product
            semantic_score = sum(a * b for a, b in zip(c.embedding or [0]*128, query_emb))
            # Lexical score (basic token overlap)
            lexical_score = len(set(query.lower().split()).intersection(set(c.content.lower().split()))) * 0.1
            hybrid_score = semantic_score * 0.7 + lexical_score * 0.3
            scored.append((hybrid_score, c))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(score, chunk) for score, chunk in scored[:top_k] if score > 0.1]

# PHASE 331 & 332 & 333 - CONTEXT ASSEMBLY & RAG GENERATION
class RAGGenerator:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.retriever = Retriever(db, get_embedding_provider())
        self.llm = get_provider()

    def answer_query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        results = self.retriever.search(self.user.company_id, request.query, request.top_k, request.source_id)
        
        if not results:
            return RAGQueryResponse(
                answer="The available business knowledge does not contain enough information to answer this question.",
                citations=[],
                insufficient_knowledge=True
            )
            
        # Context Assembly (Phase 331)
        context_parts = []
        citations = []
        for score, chunk in results:
            context_parts.append(f"[Source: {chunk.document.source_id} | Chunk: {chunk.id}]\n{chunk.content}")
            citations.append(RAGCitation(
                source_id=chunk.document.source_id,
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                score=score,
                text=chunk.content,
                page_number=chunk.page_number
            ))
            
        context_block = "\n\n".join(context_parts)
        
        system_prompt = "You are DealFlow360 RAG Assistant. Answer ONLY using the provided AUTHORIZED BUSINESS KNOWLEDGE. If it lacks info, say you lack information."
        user_prompt = f"AUTHORIZED BUSINESS KNOWLEDGE:\n{context_block}\n\nUSER QUESTION:\n{request.query}"
        
        # Generation (Phase 332)
        llm_response = self.llm.generate([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        return RAGQueryResponse(
            answer=llm_response.content or "Error generating answer.",
            citations=citations,
            insufficient_knowledge=False
        )

# SERVICE AGGREGATOR
class RAGService:
    @staticmethod
    def create_source(db: Session, user: User, source: KnowledgeSourceCreate) -> KnowledgeSource:
        db_source = KnowledgeSource(
            company_id=user.company_id,
            name=source.name,
            source_type=source.source_type,
            metadata_=source.metadata_
        )
        db.add(db_source)
        db.commit()
        db.refresh(db_source)
        return db_source
        
    @staticmethod
    def ingest_document(db: Session, user: User, source_id: uuid.UUID, file: UploadFile):
        source = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id, KnowledgeSource.company_id == user.company_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
            
        doc = KnowledgeDocument(source_id=source.id, filename=file.filename, mime_type=file.content_type)
        db.add(doc)
        db.commit()
        
        # Extraction & Processing (Phase 324)
        text = DocumentProcessor.extract_text(file)
        
        # Chunking (Phase 325)
        chunks = Chunker.chunk_text(text)
        
        # Embeddings (Phase 326)
        embedder = get_embedding_provider()
        embeddings = [embedder.embed_text(c) for c in chunks]
        
        # Store (Phase 327)
        vs = VectorStore(db)
        vs.store_chunks(doc.id, user.company_id, chunks, embeddings)
        
        doc.status = "COMPLETED"
        source.status = "COMPLETED"
        db.commit()
        return doc
