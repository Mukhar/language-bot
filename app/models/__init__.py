from sqlalchemy import Column, String, Text, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Scenario(Base):
    """
    Simple healthcare communication scenario model
    Compatible with both PostgreSQL (Supabase) and SQLite
    """
    __tablename__ = "scenarios"

    # Use String for cross-compatibility, UUID for PostgreSQL optimization
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # general, emergency, routine
    difficulty = Column(String(20), nullable=False)  # beginner, intermediate
    
    # Add timestamps for better tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Response(Base):
    """
    Simple user response with embedded evaluation
    Compatible with both PostgreSQL (Supabase) and SQLite
    """
    __tablename__ = "responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    scenario_id = Column(String(36), nullable=False, index=True)  # Foreign key reference
    response_text = Column(Text, nullable=False)
    
    # Simple embedded evaluation (no separate table needed)
    score = Column(Float, nullable=True)  # 1-10 scale
    feedback = Column(Text, nullable=True)  # Brief feedback text
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


__all__ = ["Scenario", "Response"]
