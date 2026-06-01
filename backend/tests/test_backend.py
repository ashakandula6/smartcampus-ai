"""
Backend tests for SmartCampus AI.
Run: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Set test environment before importing app
os.environ["DATABASE_URL"] = os.getenv(
    "DATABASE_URL", "postgresql://postgres:testpassword@localhost:5432/smartcampus_test"
)
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "test")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
os.environ["S3_BUCKET_NAME"] = "test-bucket"
os.environ["COGNITO_USER_POOL_ID"] = "test"
os.environ["COGNITO_CLIENT_ID"] = "test"
os.environ["SECRET_KEY"] = "test-secret"

from app.core.database import Base, get_db
from app.services.pdf_service import clean_text, chunk_text, process_pdf_to_chunks
from main import app


# ── Test DB setup ─────────────────────────────────────────────
TEST_DB_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# ── PDF service tests ─────────────────────────────────────────

def test_clean_text_removes_extra_newlines():
    text = "Hello\n\n\n\nWorld"
    result = clean_text(text)
    assert "\n\n\n" not in result


def test_chunk_text_returns_list():
    text = "This is sentence one. This is sentence two. This is sentence three. " * 50
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "text" in chunk
        assert "chunk_index" in chunk


def test_chunk_text_respects_size():
    text = "This is a test sentence. " * 100
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    for chunk in chunks:
        # Allow slight overflow from overlap
        assert len(chunk["text"]) <= 400


def test_chunk_indices_are_sequential():
    text = "Short sentence. " * 200
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i


# ── Health check test ─────────────────────────────────────────

def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
