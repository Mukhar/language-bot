from sqlalchemy import Column, String, Text, Float, DateTime
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Scenario(Base):
    """
    Simple healthcare communication scenario model
    """
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # general, emergency, routine
    difficulty = Column(String(20), nullable=False)  # beginner, intermediate


class Response(Base):
    """
    Simple user response with embedded evaluation
    """
    __tablename__ = "responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    scenario_id = Column(String, nullable=False, index=True)  # Simple foreign key reference
    response_text = Column(Text, nullable=False)
    
    # Simple embedded evaluation (no separate table needed)
    score = Column(Float, nullable=True)  # 1-10 scale
    feedback = Column(Text, nullable=True)  # Brief feedback text
    
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())


__all__ = ["Scenario", "Response"]
