from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "JewWatch API"
    PROJECT_VERSION: str = "1.0.0"
    MONGODB_URI: str = "mongodb+srv://kobiza:Basketball0506@antiisraeldbproject.ovcycfn.mongodb.net/?retryWrites=true&w=majority&appName=AntiIsraelDBProject"
    # MONGO_URI: str = "mongodb://localhost:27017"
    GDELT_UPDATE_INTERVAL: int = 15  # minutes
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
