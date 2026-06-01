from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    cognito_sub = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents = relationship("Document", back_populates="owner", cascade="all, delete")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)         # S3 object key
    faiss_index_key = Column(String)                # S3 key for FAISS index file
    total_chunks = Column(Integer, default=0)
    status = Column(String, default="processing")   # processing | ready | failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="documents")
    questions = relationship("Question", back_populates="document", cascade="all, delete")
    quizzes = relationship("Quiz", back_populates="document", cascade="all, delete")


class Question(Base):
    """Chat history — questions asked about a document."""
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    user_question = Column(Text, nullable=False)
    ai_answer = Column(Text, nullable=False)
    source_chunks = Column(JSON)    # Which chunks were used
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="questions")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    title = Column(String)
    questions_data = Column(JSON, nullable=False)   # List of MCQ dicts
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="quizzes")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    answers = Column(JSON, nullable=False)          # {question_index: chosen_option}
    score = Column(Float, nullable=False)           # 0.0 - 100.0
    weak_topics = Column(JSON)                      # Topics answered wrong
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
