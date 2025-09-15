from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..database import get_db
from ..models import Scenario
from ..schemas import ScenarioRequest, ScenarioResponse
from ..services.lm_studio import LMStudioService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("/generate", response_model=ScenarioResponse)
async def generate_scenario(
    request: ScenarioRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a simple healthcare communication scenario
    """
    try:
        # Initialize LM Studio service
        lm_studio = LMStudioService()
        
        # Generate simple scenario using LM Studio
        scenario_data = await lm_studio.generate_scenario(
            category=request.category,
            difficulty=request.difficulty
        )
        
        # Create scenario in database with simplified fields
        db_scenario = Scenario(
            id=str(uuid.uuid4()),
            title=scenario_data["title"],
            description=scenario_data["description"],
            category=scenario_data["category"],
            difficulty=scenario_data["difficulty"]
        )
        
        db.add(db_scenario)
        db.commit()
        db.refresh(db_scenario)
        
        logger.info("Simple scenario generated successfully", scenario_id=db_scenario.id)
        return db_scenario
        
    except Exception as e:
        logger.error("Failed to generate scenario", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate scenario. Please try again."
        )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific scenario by ID
    """
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    return scenario
