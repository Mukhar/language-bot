from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..database import get_db
from ..models import Response, Scenario
from ..schemas import ResponseRequest, ResponseWithEvaluation
from ..services.lm_studio import LMStudioService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/responses", tags=["responses"])


@router.post("/", response_model=ResponseWithEvaluation)
async def submit_response(
    request: ResponseRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a user response to a scenario and get immediate evaluation
    
    Simple endpoint that:
    1. Validates the scenario exists
    2. Saves the response
    3. Attempts to evaluate using AI
    4. Returns the response with evaluation
    """
    try:
        # Step 1: Check if scenario exists
        scenario = db.query(Scenario).filter(Scenario.id == request.scenario_id).first()
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )
        
        # Step 2: Create and save response
        response_id = str(uuid.uuid4())
        db_response = Response(
            id=response_id,
            scenario_id=request.scenario_id,
            response_text=request.response_text
        )
        
        db.add(db_response)
        db.commit()
        db.refresh(db_response)
        
        # Step 3: Try to evaluate the response
        try:
            lm_studio = LMStudioService()
            evaluation = await lm_studio.evaluate_response(
                scenario=scenario.__dict__,
                user_response=request.response_text
            )
            
            # Update response with evaluation
            db_response.score = evaluation["score"]
            db_response.feedback = evaluation["feedback"]
            db.commit()
            db.refresh(db_response)
            
            logger.info("Response submitted and evaluated successfully", 
                       response_id=response_id)
            
        except Exception as eval_error:
            logger.warning("Response saved but evaluation failed", 
                         response_id=response_id, 
                         error=str(eval_error))
            # Response is saved even if evaluation fails
        
        return db_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Failed to submit response", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit response. Please try again."
        )


@router.get("/{response_id}", response_model=ResponseWithEvaluation)
async def get_response(
    response_id: str, 
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific response by ID with evaluation
    
    Simple endpoint that:
    1. Validates the response ID format
    2. Fetches the response from database
    3. Returns complete response data including evaluation
    """
    try:
        # Validate UUID format (basic validation)
        if not response_id or len(response_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Response ID is required"
            )
        
        # Fetch response from database
        response = db.query(Response).filter(Response.id == response_id).first()
        
        if not response:
            logger.warning("Response not found", response_id=response_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Response not found"
            )
        
        logger.info("Response retrieved successfully", response_id=response_id)
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Failed to retrieve response", response_id=response_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve response. Please try again."
        )


@router.get("/scenario/{scenario_id}", response_model=List[ResponseWithEvaluation])
async def get_responses_for_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(default=10, le=50, ge=1, description="Number of responses to return (max 50)")
):
    """
    Retrieve all responses for a specific scenario
    
    Simple endpoint that:
    1. Validates the scenario exists
    2. Fetches all responses for that scenario
    3. Returns list of responses with evaluations
    """
    try:
        # Validate scenario exists
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )
        
        # Fetch responses for this scenario
        responses = (
            db.query(Response)
            .filter(Response.scenario_id == scenario_id)
            .order_by(Response.submitted_at.desc())  # Most recent first
            .limit(limit)
            .all()
        )
        
        logger.info("Responses retrieved for scenario", 
                   scenario_id=scenario_id, 
                   count=len(responses))
        
        return responses
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Failed to retrieve responses for scenario", 
                    scenario_id=scenario_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve responses. Please try again."
        )
