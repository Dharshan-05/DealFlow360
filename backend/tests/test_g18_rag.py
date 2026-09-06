

import pytest
import uuid
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import get_db
from app.api.v1.endpoints.deps import get_current_user
from app.models.company import Company
from app.models.user import User
from app.rag.models import KnowledgeSource, KnowledgeDocument, KnowledgeChunk

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
    company = Company(id=uuid.uuid4(), name="RAG Corp", )
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
    # Create Source
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Sales Policy", "source_type": "DOCUMENT"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Sales Policy"
    assert data["status"] == "PENDING"
    source_id = data["id"]
    
    # List Sources
    resp = client.get("/api/v1/knowledge/sources")
    assert len(resp.json()) == 1
    
    # Get Source
    resp = client.get(f"/api/v1/knowledge/sources/{source_id}")
    assert resp.json()["id"] == source_id

def test_document_ingestion_and_processing(client: TestClient, setup_rag_data):
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Test Upload", "source_type": "DOCUMENT"})
    source_id = resp.json()["id"]
    
    # Test Ingestion with a valid mock txt file
    file_content = b"This is a sales policy document. Enterprise discount is max 20%."
    files = {"file": ("policy.txt", io.BytesIO(file_content), "text/plain")}
    
    resp = client.post(f"/api/v1/knowledge/sources/{source_id}/ingest", files=files)
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"
    
def test_rag_semantic_hybrid_retrieval(client: TestClient, setup_rag_data):
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Hybrid Test", "source_type": "DOCUMENT"})
    source_id = resp.json()["id"]
    
    files = {"file": ("hybrid.txt", io.BytesIO(b"Enterprise policy requires manager approval."), "text/plain")}
    client.post(f"/api/v1/knowledge/sources/{source_id}/ingest", files=files)
    
    # Query Knowledge
    resp = client.post("/api/v1/knowledge/query", json={"query": "What does Enterprise policy require?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "citations" in data
    assert len(data["citations"]) > 0

def test_rag_cross_tenant_isolation(client: TestClient, db_session: Session, setup_rag_data):
    resp = client.post("/api/v1/knowledge/sources", json={"name": "Secret", "source_type": "DOCUMENT"})
    source_id = resp.json()["id"]
    files = {"file": ("secret.txt", io.BytesIO(b"Secret 42"), "text/plain")}
    client.post(f"/api/v1/knowledge/sources/{source_id}/ingest", files=files)
    
    # Create Malicious User in another company
    comp2 = Company(id=uuid.uuid4(), name="Evil Corp", )
    db_session.add(comp2)
    user2 = User(id=uuid.uuid4(), email=f"evil_{uuid.uuid4()}@evil.corp", password_hash="x", company_id=comp2.id, first_name="Test", last_name="Admin")
    db_session.add(user2)
    db_session.commit()
    
    app.dependency_overrides[get_current_user] = lambda: user2
    resp = client.post("/api/v1/knowledge/query", json={"query": "Secret 42"})
    assert resp.status_code == 200
    assert resp.json()["insufficient_knowledge"] is True
    assert len(resp.json()["citations"]) == 0
