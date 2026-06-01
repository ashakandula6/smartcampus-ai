from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine
from app.models.models import Base
from app.api import documents, chat, quiz, users
from app.services.s3_service import s3_service
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables and S3 bucket
    Base.metadata.create_all(bind=engine)
    s3_service.ensure_bucket_exists()
    print(f"✅ SmartCampus AI started — {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # Shutdown
    print("SmartCampus AI shutting down...")


app = FastAPI(
    title="SmartCampus AI API",
    description="AI-powered study assistant for students",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — update origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",           
        "http://127.0.0.1:5173",
        "https://your-frontend-domain.com",  # Update this
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"message": "SmartCampus AI API", "docs": "/docs"}
