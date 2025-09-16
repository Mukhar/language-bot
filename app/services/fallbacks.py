"""
Fallback methods for LM Studio service.

This module contains all fallback responses used when LM Studio is unavailable
or when parsing LM Studio responses fails.
"""

from typing import Dict, Any
from ..prompts import (
    FALLBACK_SCENARIO_TITLE,
    FALLBACK_SCENARIO_DESCRIPTION,
    FALLBACK_EVALUATION_SCORE,
    FALLBACK_EVALUATION_FEEDBACK
)


def get_simple_fallback_scenario(category: str, difficulty: str) -> Dict[str, Any]:
    """
    Return a simple fallback scenario when LM Studio is unavailable
    
    Uses configuration from prompts.py for easy modification.
    
    Args:
        category: The scenario category (general, emergency, routine)
        difficulty: The difficulty level (beginner, intermediate)
        
    Returns:
        Dict containing simple scenario with title, description, category, and difficulty
    """
    fallback_scenarios = {
        "emergency": {
            "title": "Emergency Communication",
            "description": "Practice communicating with a patient in an emergency setting."
        },
        "routine": {
            "title": "Routine Check-up",
            "description": "Practice communication during a regular patient visit."
        },
        "general": {
            "title": FALLBACK_SCENARIO_TITLE,
            "description": FALLBACK_SCENARIO_DESCRIPTION
        }
    }
    
    scenario = fallback_scenarios.get(category, fallback_scenarios["general"])
    scenario.update({
        "category": category,
        "difficulty": difficulty
    })
    
    return scenario


def get_simple_fallback_evaluation() -> Dict[str, Any]:
    """
    Return a simple fallback evaluation when LM Studio is unavailable
    
    Uses configuration from prompts.py for easy modification.
    
    Returns:
        Dict containing simple evaluation with score and feedback
    """
    return {
        "score": FALLBACK_EVALUATION_SCORE,
        "feedback": FALLBACK_EVALUATION_FEEDBACK
    }


def get_fallback_scenario(category: str, difficulty: str) -> Dict[str, Any]:
    """
    Return a comprehensive fallback scenario when LM Studio is unavailable
    
    Provides detailed scenario information including patient background,
    medical context, and communication challenges.
    
    Args:
        category: The scenario category (general, emergency, routine)
        difficulty: The difficulty level (beginner, intermediate)
        
    Returns:
        Dict containing comprehensive scenario information
    """
    fallback_scenarios = {
        "emergency": {
            "title": "Emergency Department Communication",
            "description": "Practice communicating with a patient in an emergency setting",
            "patient_background": "45-year-old patient presenting with chest pain, appears anxious",
            "medical_context": "Initial assessment suggests possible cardiac event, requires immediate evaluation",
            "communication_challenge": "Calm the patient while gathering critical information efficiently"
        },
        "general": {
            "title": "Routine Check-up Discussion",
            "description": "Practice routine patient communication during a regular visit",
            "patient_background": "35-year-old patient for annual check-up, generally healthy",
            "medical_context": "Routine physical examination, discussing lifestyle and preventive care",
            "communication_challenge": "Engage patient in discussing lifestyle modifications and health goals"
        }
    }
    
    scenario = fallback_scenarios.get(category, fallback_scenarios["general"])
    scenario.update({
        "category": category,
        "difficulty": difficulty
    })
    
    return scenario


def get_fallback_evaluation() -> Dict[str, Any]:
    """
    Return a comprehensive fallback evaluation when LM Studio is unavailable
    
    Provides detailed evaluation with multiple scoring dimensions
    and constructive feedback.
    
    Returns:
        Dict containing comprehensive evaluation information
    """
    return {
        "score": 7.0,
        "empathy_score": 7.0,
        "clarity_score": 7.0,
        "professionalism_score": 7.0,
        "medical_accuracy_score": 7.0,
        "feedback": "Your response demonstrates good communication skills. Due to technical limitations, a detailed evaluation is not available at this time. Please try again later for comprehensive feedback.",
        "improvement_suggestions": [
            "Continue practicing active listening",
            "Focus on clear, concise communication",
            "Maintain professional empathy"
        ]
    }