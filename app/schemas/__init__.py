from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class ScenarioRequest(BaseModel):
    """
    Request schema for simple scenario generation
    """
    category: str = Field(..., description="Basic category: general, emergency, routine")
    difficulty: str = Field(..., description="Difficulty level: beginner, intermediate")
    
    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v):
        allowed_levels = ['beginner', 'intermediate']
        if v not in allowed_levels:
            raise ValueError(f'Difficulty must be one of: {", ".join(allowed_levels)}')
        return v
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        allowed_categories = ['general', 'emergency', 'routine']
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        return v


class ScenarioResponse(BaseModel):
    """
    Response schema for simple scenarios
    """
    id: str
    title: str
    description: str
    category: str
    difficulty: str
    
    model_config = ConfigDict(from_attributes=True)


class ResponseRequest(BaseModel):
    """
    Request schema for submitting user responses
    """
    scenario_id: str = Field(..., description="ID of the scenario being responded to")
    response_text: str = Field(..., description="User's response", max_length=2000, min_length=10)
    
    @field_validator('response_text')
    @classmethod
    def validate_response_text(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Response must be at least 10 characters long')
        return v.strip()


class ResponseWithEvaluation(BaseModel):
    """
    Response schema with embedded evaluation
    """
    id: str
    scenario_id: str
    response_text: str
    score: Optional[float] = Field(None, ge=1.0, le=10.0)
    feedback: Optional[str] = None
    submitted_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """
    Standard error response schema
    """
    detail: str


class HealthResponse(BaseModel):
    """
    Health check response schema
    """
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
