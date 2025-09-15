from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import json

from ..database import get_db
from ..models import Evaluation, Response, Scenario
from ..schemas import EvaluationRequest, EvaluationResponse
from ..services.lm_studio import LMStudioService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


@router.post("/", response_model=EvaluationResponse)
async def create_evaluation(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate a user response using AI
    """
    try:
        # Get the response and associated scenario
        response = db.query(Response).filter(Response.id == request.response_id).first()
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Response not found"
            )
        
        # Check if evaluation already exists
        existing_evaluation = db.query(Evaluation).filter(
            Evaluation.response_id == request.response_id
        ).first()
        
        if existing_evaluation:
            return existing_evaluation
        
        # Get scenario for context
        scenario = db.query(Scenario).filter(Scenario.id == response.scenario_id).first()
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated scenario not found"
            )
        
        # Initialize LM Studio service
        lm_studio = LMStudioService()
        
        # Prepare scenario data for evaluation
        scenario_data = {
            "title": scenario.title,
            "communication_challenge": scenario.communication_challenge,
            "patient_background": scenario.patient_background,
            "medical_context": scenario.medical_context
        }
        
        # Get evaluation from LM Studio
        evaluation_data = await lm_studio.evaluate_response(
            scenario=scenario_data,
            user_response=response.response_text
        )
        
        # Create evaluation record
        db_evaluation = Evaluation(
            id=str(uuid.uuid4()),
            response_id=request.response_id,
            overall_score=evaluation_data["overall_score"],
            empathy_score=evaluation_data["empathy_score"],
            clarity_score=evaluation_data["clarity_score"],
            professionalism_score=evaluation_data["professionalism_score"],
            medical_accuracy_score=evaluation_data["medical_accuracy_score"],
            detailed_feedback=evaluation_data["detailed_feedback"],
            improvement_suggestions=json.dumps(evaluation_data.get("improvement_suggestions", []))
        )
        
        db.add(db_evaluation)
        db.commit()
        db.refresh(db_evaluation)
        
        logger.info("Evaluation created successfully", evaluation_id=db_evaluation.id)
        
        # Convert improvement_suggestions back to list for response
        improvement_suggestions_raw = getattr(db_evaluation, 'improvement_suggestions', None)
        improvement_suggestions = json.loads(improvement_suggestions_raw) if improvement_suggestions_raw else []
        
        response_data = {
            "id": db_evaluation.id,
            "response_id": db_evaluation.response_id,
            "overall_score": db_evaluation.overall_score,
            "empathy_score": db_evaluation.empathy_score,
            "clarity_score": db_evaluation.clarity_score,
            "professionalism_score": db_evaluation.professionalism_score,
            "medical_accuracy_score": db_evaluation.medical_accuracy_score,
            "detailed_feedback": db_evaluation.detailed_feedback,
            "improvement_suggestions": improvement_suggestions,
            "evaluated_at": db_evaluation.evaluated_at
        }
        
        return EvaluationResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create evaluation", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate response. Please try again."
        )


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific evaluation by ID
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    # Convert improvement_suggestions back to list
    improvement_suggestions_raw = getattr(evaluation, 'improvement_suggestions', None)
    improvement_suggestions = json.loads(improvement_suggestions_raw) if improvement_suggestions_raw else []
    
    response_data = {
        "id": evaluation.id,
        "response_id": evaluation.response_id,
        "overall_score": evaluation.overall_score,
        "empathy_score": evaluation.empathy_score,
        "clarity_score": evaluation.clarity_score,
        "professionalism_score": evaluation.professionalism_score,
        "medical_accuracy_score": evaluation.medical_accuracy_score,
        "detailed_feedback": evaluation.detailed_feedback,
        "improvement_suggestions": improvement_suggestions,
        "evaluated_at": evaluation.evaluated_at
    }
    
    return EvaluationResponse(**response_data)


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_response(
    response_id: str,
    db: Session = Depends(get_db)
):
    """
    Convenient endpoint to evaluate a response directly by response_id
    """
    request = EvaluationRequest(response_id=response_id)
    return await create_evaluation(request, db)
