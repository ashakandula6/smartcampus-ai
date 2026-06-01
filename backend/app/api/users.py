from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import verify_token, get_current_user_id
from app.models.models import User, QuizAttempt
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/users", tags=["users"])


class RegisterRequest(BaseModel):
    name: str
    email: str


@router.post("/register")
async def register_user(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    cognito_sub = get_current_user_id(token_payload)

    existing = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    if existing:
        return {"message": "Already registered", "user_id": existing.id}

    user = User(
        cognito_sub=cognito_sub,
        email=body.email,
        name=body.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Registered successfully", "user_id": user.id}


@router.get("/me")
async def get_me(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    cognito_sub = get_current_user_id(token_payload)
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Call POST /api/v1/users/register first."
        )

    total_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user.id).count()
    recent_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id)
        .order_by(QuizAttempt.completed_at.desc())
        .limit(5)
        .all()
    )
    avg_score = (
        sum(a.score for a in recent_attempts) / len(recent_attempts)
        if recent_attempts else 0
    )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": str(user.created_at),
        "stats": {
            "total_quizzes": total_attempts,
            "avg_score": round(avg_score, 1),
            "documents_count": len(user.documents),
        },
    }