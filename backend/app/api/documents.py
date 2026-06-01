import uuid
import traceback
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import verify_token, get_current_user_id
from app.models.models import Document, User
from app.services.s3_service import s3_service
from app.services.pdf_service import process_pdf_to_chunks
from app.services.rag_service import build_and_store_index
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    total_chunks: int
    created_at: str

    class Config:
        from_attributes = True


def process_document_background(document_id: str, pdf_bytes: bytes, db_url: str):
    """Background task: parse PDF → build FAISS index → update DB."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Fix SQLite threading issue
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    engine = create_engine(db_url, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print(f"\n{'='*50}")
        print(f"[BG TASK] Starting processing for doc: {document_id}")

        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"[BG TASK] ERROR: Document {document_id} not found in DB")
            return

        # Step 1: Parse and chunk PDF
        print(f"[BG TASK] Step 1: Parsing PDF ({len(pdf_bytes)} bytes)...")
        chunks = process_pdf_to_chunks(pdf_bytes)
        print(f"[BG TASK] Step 1 done: {len(chunks)} chunks created")

        # Step 2: Build and store FAISS index
        print(f"[BG TASK] Step 2: Building FAISS index...")
        faiss_key = build_and_store_index(document_id, chunks)
        print(f"[BG TASK] Step 2 done: index saved at {faiss_key}")

        # Step 3: Update DB record
        doc.total_chunks = len(chunks)
        doc.faiss_index_key = faiss_key
        doc.status = "ready"
        db.commit()
        print(f"[BG TASK] SUCCESS: doc {document_id} is ready with {len(chunks)} chunks")
        print(f"{'='*50}\n")

    except Exception as e:
        print(f"\n{'='*50}")
        print(f"[BG TASK] FAILED for doc {document_id}")
        print(f"[BG TASK] Error: {str(e)}")
        print(f"[BG TASK] Full traceback:")
        print(traceback.format_exc())
        print(f"{'='*50}\n")

        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "failed"
                db.commit()
        except Exception as db_err:
            print(f"[BG TASK] Could not update status to failed: {db_err}")
    finally:
        db.close()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    """Upload a PDF lecture note."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if file.size and file.size > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 20MB.")

    user_id = get_current_user_id(token_payload)
    user = db.query(User).filter(User.cognito_sub == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Call POST /api/v1/users/register first."
        )

    pdf_bytes = await file.read()
    print(f"[UPLOAD] Received {file.filename} ({len(pdf_bytes)} bytes) for user {user.id}")

    document_id = str(uuid.uuid4())
    s3_key = f"pdfs/{user.id}/{document_id}/{file.filename}"

    # Try S3 upload — skip gracefully if not configured
    try:
        s3_service.upload_pdf(pdf_bytes, s3_key)
        print(f"[UPLOAD] S3 upload OK: {s3_key}")
    except Exception as e:
        print(f"[UPLOAD] S3 upload SKIPPED (local mode): {e}")
        s3_key = f"local/{document_id}/{file.filename}"  # fake key for local dev

    # Save DB record
    doc = Document(
        id=document_id,
        user_id=user.id,
        filename=file.filename,
        s3_key=s3_key,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Kick off background processing
    from app.core.config import get_settings
    settings = get_settings()
    background_tasks.add_task(
        process_document_background,
        document_id,
        pdf_bytes,
        settings.DATABASE_URL,
    )

    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        total_chunks=doc.total_chunks,
        created_at=str(doc.created_at),
    )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    user_id = get_current_user_id(token_payload)
    user = db.query(User).filter(User.cognito_sub == user_id).first()
    if not user:
        return []

    docs = db.query(Document).filter(Document.user_id == user.id).all()
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            status=d.status,
            total_chunks=d.total_chunks,
            created_at=str(d.created_at),
        )
        for d in docs
    ]


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": doc.status, "total_chunks": doc.total_chunks}


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    user_id = get_current_user_id(token_payload)
    user = db.query(User).filter(User.cognito_sub == user_id).first()
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user.id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        s3_service.delete_object(doc.s3_key)
        if doc.faiss_index_key:
            s3_service.delete_object(doc.faiss_index_key)
    except Exception as e:
        print(f"[DELETE] S3 cleanup error (non-fatal): {e}")

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}