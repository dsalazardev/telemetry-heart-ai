from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/telemetry_heart"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # ChromaDB
    CHROMA_PATH: str = "./chroma_db"
    
    # Model
    MODEL_PATH: str = "./data/model.pkl"
    
    # Environment
    ENV: str = "development"  # development, production, test
    
    # Microservice
    PORT: int = 8001
    HOST: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
