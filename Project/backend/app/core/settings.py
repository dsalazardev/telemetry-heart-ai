import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str
    MICROSERVICE_URL: str = "http://localhost:8001"
    UMBRALES_PATH: str = str(Path(__file__).parent.parent / "config" / "umbrales.json")
    SECRET_KEY: str = "triaje-cardiovascular-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEVICE_TOKEN_EXPIRE_DAYS: int = 30

    INTERNAL_TOKEN: str = "dev-token-cambiar-en-prod"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        extra = "ignore"


settings = Settings()
