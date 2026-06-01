from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict

from app.core.database import get_db
from app.core.security import verify_token, get_current_user_id
from app.models.models import Document, Quiz, QuizAttempt, User
from app.services.rag_service import retrieve_relevant_chunks
from app.services.claude_service import generate_quiz, analyze_weak_topics

router = APIRouter(prefix="/quiz", tags=["quiz"])


class GenerateQuizRequest(BaseModel):
    document_id: str
    num_questions: int = 10


class SubmitQuizRequest(BaseModel):
    quiz_id: str
    answers: Dict[str, str]  # {question_index: "A"/"B"/"C"/"D"}


class QuizAttemptResponse(BaseModel):
    attempt_id: str
    score: float
    total_questions: int
    correct_count: int
    weak_topics_analysis: str
    results: List[Dict]


@router.post("/generate")
async def generate_quiz_endpoint(
    body: GenerateQuizRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    """Generate a quiz from a document's content using Claude."""
    user_id = get_current_user_id(token_payload)
    user = db.query(User).filter(User.cognito_sub == user_id).first()

    doc = db.query(Document).filter(
        Document.id == body.document_id,
        Document.user_id == user.id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail="Document not ready yet")

    # Get broad chunks for quiz generation (not query-specific)
    chunks = retrieve_relevant_chunks(
        faiss_index_s3_key=doc.faiss_index_key,
        query="main concepts key topics overview",  # broad query to get representative chunks
        top_k=15,
    )

    # Generate quiz with Claude
    quiz_data = generate_quiz(chunks, num_questions=body.num_questions)

    # Save to DB
    quiz = Quiz(
        document_id=doc.id,
        title=quiz_data.get("title", f"Quiz on {doc.filename}"),
        questions_data=quiz_data["questions"],
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "questions": [
            {
                "index": i,
                "question": q["question"],
                "options": q["options"],
                "topic": q.get("topic", ""),
            }
            for i, q in enumerate(quiz.questions_data)
        ],
    }


@router.post("/submit", response_model=QuizAttemptResponse)
async def submit_quiz(
    body: SubmitQuizRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    """Submit quiz answers, get score and weak topic analysis."""
    user_id = get_current_user_id(token_payload)
    user = db.query(User).filter(User.cognito_sub == user_id).first()

    quiz = db.query(Quiz).filter(Quiz.id == body.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz.questions_data
    results = []
    wrong_questions = []
    correct_count = 0

    for i, question in enumerate(questions):
        student_answer = body.answers.get(str(i), "")
        correct_answer = question["correct_answer"]
        is_correct = student_answer.upper() == correct_answer.upper()

        if is_correct:
            correct_count += 1
        else:
            wrong_questions.append(question)

        results.append({
            "index": i,
            "question": question["question"],
            "your_answer": student_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": question.get("explanation", ""),
            "topic": question.get("topic", ""),
        })

    score = (correct_count / len(questions)) * 100 if questions else 0

    # AI analysis of weak areas
    weak_analysis = analyze_weak_topics(wrong_questions)

    # Save attempt
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=user.id,
        answers=body.answers,
        score=score,
        weak_topics=[q.get("topic") for q in wrong_questions],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return QuizAttemptResponse(
        attempt_id=attempt.id,
        score=score,
        total_questions=len(questions),
        correct_count=correct_count,
        weak_topics_analysis=weak_analysis,
        results=results,
    )


@router.get("/history")
async def get_quiz_history(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    """Get all quiz attempts for dashboard."""
    user_id = get_current_user_id(token_payload)
    user = db.query(User).filter(User.cognito_sub == user_id).first()
    if not user:
        return []

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id)
        .order_by(QuizAttempt.completed_at.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "attempt_id": a.id,
            "quiz_id": a.quiz_id,
            "score": a.score,
            "weak_topics": a.weak_topics,
            "completed_at": str(a.completed_at),
        }
        for a in attempts
    ]
