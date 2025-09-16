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
    
    Enhanced with comprehensive logging for debugging and monitoring.
    """
    request_id = str(uuid.uuid4())[:8]  # Short ID for tracking this request
    
    logger.info(
        "Starting scenario generation request",
        request_id=request_id,
        category=request.category,
        difficulty=request.difficulty
    )
    
    try:
        # Initialize LM Studio service
        logger.debug("Initializing LM Studio service", request_id=request_id)
        lm_studio = LMStudioService()
        
        # Generate simple scenario using LM Studio
        logger.info(
            "Requesting scenario from LM Studio",
            request_id=request_id,
            category=request.category,
            difficulty=request.difficulty
        )
        
        scenario_data = await lm_studio.generate_scenario(
            category=request.category,
            difficulty=request.difficulty
        )
        
        logger.info(
            "LM Studio scenario generated successfully",
            request_id=request_id,
            title=scenario_data.get("title", "N/A")[:50] + "..." if len(scenario_data.get("title", "")) > 50 else scenario_data.get("title", "N/A"),
            description_length=len(scenario_data.get("description", "")),
            has_fallback=scenario_data.get("title") == "General Healthcare Communication"
        )
        
        # Create scenario in database with simplified fields
        scenario_id = str(uuid.uuid4())
        logger.debug(
            "Creating scenario in database",
            request_id=request_id,
            scenario_id=scenario_id
        )
        
        db_scenario = Scenario(
            id=scenario_id,
            title=scenario_data["title"],
            description=scenario_data["description"],
            category=scenario_data["category"],
            difficulty=scenario_data["difficulty"]
        )
        
        db.add(db_scenario)
        db.commit()
        db.refresh(db_scenario)
        
        logger.info(
            "Scenario generated and saved successfully",
            request_id=request_id,
            scenario_id=db_scenario.id,
            category=db_scenario.category,
            difficulty=db_scenario.difficulty,
            title=(db_scenario.title[:50] + "...") if len(str(db_scenario.title)) > 50 else str(db_scenario.title)
        )
        
        return db_scenario
        
    except HTTPException as he:
        logger.warning(
            "HTTP exception during scenario generation",
            request_id=request_id,
            status_code=he.status_code,
            detail=he.detail
        )
        db.rollback()
        raise
        
    except Exception as e:
        logger.error(
            "Unexpected error during scenario generation",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            category=request.category,
            difficulty=request.difficulty,
            exc_info=True
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate scenario. Please try again."
        )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific scenario by ID
    
    Enhanced with logging for debugging and monitoring.
    """
    logger.info("Retrieving scenario", scenario_id=scenario_id)
    
    try:
        # Validate scenario ID format
        if not scenario_id or len(scenario_id.strip()) == 0:
            logger.warning("Invalid scenario ID provided", scenario_id=scenario_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scenario ID is required"
            )
        
        # Query database for scenario
        logger.debug("Querying database for scenario", scenario_id=scenario_id)
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            logger.warning("Scenario not found in database", scenario_id=scenario_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )
        
        logger.info(
            "Scenario retrieved successfully",
            scenario_id=scenario_id,
            category=scenario.category,
            difficulty=scenario.difficulty,
            title=(str(scenario.title)[:50] + "...") if len(str(scenario.title)) > 50 else str(scenario.title)
        )
        
        return scenario
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Unexpected error retrieving scenario",
            scenario_id=scenario_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scenario. Please try again."
        )
