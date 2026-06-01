from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.core.security import verify_token, get_current_user_id
from app.models.models import Document, Question, User
from app.services.rag_service import retrieve_relevant_chunks
from app.services.claude_service import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


class AskRequest(BaseModel):
    document_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    source_chunks: List[dict]
    question_id: str


class ChatHistoryItem(BaseModel):
    id: str
    question: str
    answer: str
    created_at: str


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    body: AskRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    """Ask a question about a document using RAG + Claude."""
    user_id = get_current_user_id(token_payload)
    user = db.query(User).filter(User.cognito_sub == user_id).first()

    # Verify document belongs to user and is ready
    doc = db.query(Document).filter(
        Document.id == body.document_id,
        Document.user_id == user.id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Document is still {doc.status}. Wait for processing to complete.",
        )
    if not doc.faiss_index_key:
        raise HTTPException(status_code=500, detail="Document index not found")

    # Retrieve relevant chunks via FAISS
    relevant_chunks = retrieve_relevant_chunks(
        faiss_index_key=doc.faiss_index_key,
        query=body.question,
        top_k=5,
    )

    if not relevant_chunks:
        return AskResponse(
            answer="No relevant content found in your notes for this question.",
            source_chunks=[],
            question_id="",
        )

    # Generate answer with Claude
    answer = answer_question(body.question, relevant_chunks)

    # Save to DB
    qa = Question(
        document_id=doc.id,
        user_question=body.question,
        ai_answer=answer,
        source_chunks=[{"chunk_index": c["chunk_index"], "score": c.get("score", 0)} for c in relevant_chunks],
    )
    db.add(qa)
    db.commit()
    db.refresh(qa)

    return AskResponse(
        answer=answer,
        source_chunks=relevant_chunks,
        question_id=qa.id,
    )


@router.get("/{document_id}/history", response_model=List[ChatHistoryItem])
async def get_chat_history(
    document_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    """Get question-answer history for a document."""
    questions = (
        db.query(Question)
        .filter(Question.document_id == document_id)
        .order_by(Question.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        ChatHistoryItem(
            id=q.id,
            question=q.user_question,
            answer=q.ai_answer,
            created_at=str(q.created_at),
        )
        for q in questions
    ]
