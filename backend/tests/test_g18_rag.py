import os
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import get_db
from app.api.v1.endpoints.deps import get_current_user
from app.models.company import Company
from app.models.user import User
from app.rag.models import KnowledgeSource, KnowledgeDocument, KnowledgeChunk
from app.rag.service import Retriever, Reranker, get_embedding_provider, get_vector_store

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/dealflow360"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def setup_rag_data(db_session: Session):
    company = Company(id=uuid.uuid4(), name="RAG Corp")
    db_session.add(company)
    db_session.commit()

    user = User(
        id=uuid.uuid4(), email=f"admin_{uuid.uuid4()}@rag.corp", password_hash="hash",
        company_id=company.id, first_name="Test", last_name="Admin", is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    return {"company": company, "user": user}

@pytest.fixture
def client(setup_rag_data, db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    def override_get_current_user():
        return setup_rag_data["user"]
        
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()

def test_rag_source_crud(client: TestClient, setup_rag_data):
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Sales Policy", "source_type": "DOCUMENT"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "PENDING"

def test_document_ingestion_and_processing(client: TestClient, setup_rag_data):
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Test Upload", "source_type": "DOCUMENT"})
    source_id = resp.json()["id"]
    files = {"file": ("policy.txt", io.BytesIO(b"Enterprise discount is max 20%."), "text/plain")}
    resp = client.post(f"/api/v1/knowledge/sources/{source_id}/ingest", files=files)
    assert resp.status_code == 200

def test_rag_semantic_hybrid_retrieval(client: TestClient, setup_rag_data):
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Hybrid Test", "source_type": "DOCUMENT"})
    source_id = resp.json()["id"]
    files = {"file": ("hybrid.txt", io.BytesIO(b"Enterprise policy requires manager approval."), "text/plain")}
    client.post(f"/api/v1/knowledge/sources/{source_id}/ingest", files=files)
    
    resp = client.post("/api/v1/knowledge/query", json={"query": "What does Enterprise policy require?"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["citations"]) > 0
    # Citation Security Check
    assert "chunk_id" in data["citations"][0]

def test_rag_cross_tenant_isolation(client: TestClient, db_session: Session, setup_rag_data):
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Secret", "source_type": "DOCUMENT"})
    source_id = resp.json()["id"]
    files = {"file": ("secret.txt", io.BytesIO(b"Secret 42"), "text/plain")}
    client.post(f"/api/v1/knowledge/sources/{source_id}/ingest", files=files)
    
    comp2 = Company(id=uuid.uuid4(), name="Evil Corp")
    db_session.add(comp2)
    user2 = User(id=uuid.uuid4(), email=f"evil_{uuid.uuid4()}@evil.corp", password_hash="x", company_id=comp2.id, first_name="Test", last_name="Evil")
    db_session.add(user2)
    db_session.commit()
    
    app.dependency_overrides[get_current_user] = lambda: user2
    resp = client.post("/api/v1/knowledge/query", json={"query": "Secret 42"})
    assert resp.status_code == 200
    assert resp.json()["insufficient_knowledge"] is True

def test_true_reranking_blocker_330(db_session: Session, setup_rag_data):
    company_id = setup_rag_data["company"].id
    doc_id = uuid.uuid4()
    
    # Create two mock chunks
    c1 = KnowledgeChunk(id=uuid.uuid4(), document_id=doc_id, company_id=company_id, chunk_index=0, content="Banana is a fruit.", embedding=[0.5]*128)
    c2 = KnowledgeChunk(id=uuid.uuid4(), document_id=doc_id, company_id=company_id, chunk_index=1, content="Apple is also a fruit.", embedding=[0.6]*128)
    
    # Original scores
    candidates = [(0.8, c1), (0.9, c2)] 
    # c2 has higher semantic score initially.
    
    # Rerank with query targeting c1 exactly
    reranked = Reranker.rerank("Banana", candidates)
    
    # Prove rerank_score exists and ranking can differ
    assert "rerank_score" in reranked[0]
    assert "original_score" in reranked[0]
    # Banana should win due to exact term/phrase match boosting its score
    assert reranked[0]["chunk"].id == c1.id
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]

def test_copilot_e2e_rag_tool(client: TestClient, setup_rag_data):
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Tools", "source_type": "DOCUMENT"})
    files = {"file": ("tools.txt", io.BytesIO(b"Company vacation is 20 days."), "text/plain")}
    client.post(f"/api/v1/knowledge/sources/{resp.json()['id']}/ingest", files=files)
    
    # Hit the orchestrator action endpoint
    req = {
        "deal_id": None,
        "message": "How many days is company vacation?",
        "context": {}
    }
    action_resp = client.post("/api/v1/ai/query", json=req)
    assert action_resp.status_code == 200
    data = action_resp.json()
    assert "answer" in data
