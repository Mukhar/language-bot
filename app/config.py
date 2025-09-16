from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    # Database - Supabase PostgreSQL
    database_url: str = "sqlite:///./healthcare_bot.db"  # Fallback to SQLite
    
    # Supabase Configuration
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_db_password: str = ""
    
    # PostgreSQL/Supabase Database Configuration (when using direct connection)
    postgres_host: str = ""
    postgres_port: int = 5432
    postgres_db: str = ""
    postgres_user: str = ""
    postgres_password: str = ""
    
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
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
    
    def get_database_url(self) -> str:
        """
        Get the appropriate database URL based on configuration
        Priority: 
        1. DATABASE_URL environment variable
        2. Supabase direct connection
        3. PostgreSQL connection parameters
        4. Fallback to SQLite
        """
        # If DATABASE_URL is explicitly set, use it
        if self.database_url != "sqlite:///./healthcare_bot.db":
            return self.database_url
        
        # Try to build Supabase URL from components
        if self.postgres_host and self.postgres_user and self.postgres_password and self.postgres_db:
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        
        # Fallback to SQLite
        return self.database_url


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
