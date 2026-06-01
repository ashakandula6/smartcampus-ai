from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "SmartCampus AI"
    APP_VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./smartcampus.db"
    
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str = "smartcampus-pdfs"

    # Cognito
    COGNITO_REGION: str = "ap-south-1"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    
    GROQ_API_KEY: str = ""

    # Dev mode — bypasses Cognito auth locally
    DEV_MODE: bool = False

    # Secret key (used for signing if needed)
    SECRET_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"          # ← this is the key fix — ignores unknown .env fields


@lru_cache()
def get_settings():
    return Settings()