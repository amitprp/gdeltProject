from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "JewWatch API"
    PROJECT_VERSION: str = "1.0.0"
    MONGODB_URL: str = "mongodb+srv://amitprp:KynQcr9eZnR298iw@jewwatch.2pzabjy.mongodb.net/JewWatch"
    GDELT_UPDATE_INTERVAL: int = 15  # minutes
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
