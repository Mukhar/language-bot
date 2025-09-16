from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from typing import Generator
import os
from dotenv import load_dotenv
from .config import get_settings
import structlog

load_dotenv()

logger = structlog.get_logger()

# Get settings instance
settings = get_settings()

# Database URL with Supabase support and fallback
DATABASE_URL = settings.get_database_url()

def create_engine_with_fallback():
    """Create database engine with fallback to SQLite if PostgreSQL fails"""
    global DATABASE_URL
    
    if "postgresql" in DATABASE_URL:
        # try:
            # Try PostgreSQL first
            logger.info("Attempting to connect to PostgreSQL/Supabase")
            # engine = create_engine(
            #     DATABASE_URL,
            #     poolclass=QueuePool,
            #     pool_size=5,
            #     max_overflow=10,
            #     pool_pre_ping=True,
            #     pool_recycle=300,
            #     echo=settings.debug,
            #     connect_args={"connect_timeout": 10}  # 10 second timeout
            # )
            
            # Test the connection
            # from sqlalchemy import text
            # with engine.connect() as conn:
            #     conn.execute(text("SELECT 1"))
            
            # logger.info("Successfully connected to PostgreSQL/Supabase")
            # return engine
            
        # except Exception as e:
            # logger.warning(
            #     "Failed to connect to PostgreSQL/Supabase, falling back to SQLite",
            #     error=str(e)
            # )
            # Fallback to SQLite
            DATABASE_URL = "sqlite:///./healthcare_bot.db"
    
    # Use SQLite (either as fallback or original choice)
    logger.info("Using SQLite database")
    return create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.debug
    )

# Create engine with fallback
engine = create_engine_with_fallback()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database using SQLAlchemy metadata
    No longer using Alembic migrations - tables created directly
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


def initialize_database():
    """
    Initialize the database by creating tables
    Call this on application startup
    """
    # Import models to register them with Base metadata
    from .models import Scenario, Response
    create_tables()
