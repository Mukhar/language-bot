from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    # Database
    database_url: str = "sqlite:///./healthcare_bot.db"
    
    # LM Studio Configuration
    lm_studio_base_url: str = "http://localhost:1234"
    lm_studio_api_key: str = ""
    
    # JWT Configuration
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Settings
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    # Development Settings
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
