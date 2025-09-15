import httpx
import json
import os
from typing import Dict, Any, Optional
from ..config import get_settings
from ..prompts import (
    SCENARIO_SYSTEM_PROMPT,
    SCENARIO_USER_PROMPT_TEMPLATE,
    EVALUATION_SYSTEM_PROMPT,
    EVALUATION_USER_PROMPT_TEMPLATE,
    FALLBACK_SCENARIO_TITLE,
    FALLBACK_SCENARIO_DESCRIPTION,
    FALLBACK_EVALUATION_SCORE,
    FALLBACK_EVALUATION_FEEDBACK,
    DEFAULT_SCENARIO_TEMPERATURE,
    DEFAULT_SCENARIO_MAX_TOKENS,
    DEFAULT_EVALUATION_TEMPERATURE,
    DEFAULT_EVALUATION_MAX_TOKENS
)
import structlog

logger = structlog.get_logger()


class LMStudioError(Exception):
    """Custom exception for LM Studio related errors"""
    pass


class LMStudioService:
    """
    Service class for communicating with LM Studio local LLM
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.lm_studio_base_url
        self.api_key = self.settings.lm_studio_api_key
        self.timeout = 30.0
        
    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to LM Studio API
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error("LM Studio request timeout", url=url)
            raise LMStudioError("Request to LM Studio timed out")
            
        except httpx.HTTPStatusError as e:
            logger.error("LM Studio HTTP error", status_code=e.response.status_code, url=url)
            raise LMStudioError(f"LM Studio API error: {e.response.status_code}")
            
        except httpx.RequestError as e:
            logger.error("LM Studio connection error", error=str(e), url=url)
            raise LMStudioError(f"Failed to connect to LM Studio: {str(e)}")
    
    async def generate_scenario(
        self, 
        category: str = "general", 
        difficulty: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Generate a simple healthcare communication scenario using LM Studio
        
        Simple method that generates scenarios with basic prompts.
        Easy to modify for different use cases.
        """
        # Build simple prompt
        prompt = self._build_simple_scenario_prompt(category, difficulty)
        
        # Simple LM Studio request payload
        payload = {
            "model": "local-model",  # Configure this in your LM Studio
            "messages": [
                {
                    "role": "system",
                    "content": SCENARIO_SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": DEFAULT_SCENARIO_TEMPERATURE,
            "max_tokens": DEFAULT_SCENARIO_MAX_TOKENS,
            "stream": False
        }
        
        try:
            # Make request to LM Studio
            response = await self._make_request("/v1/chat/completions", payload)
            scenario_text = response["choices"][0]["message"]["content"]
            
            # Parse the response
            return self._parse_simple_scenario_response(scenario_text, category, difficulty)
            
        except Exception as e:
            logger.error("Failed to generate scenario", error=str(e))
            # Return simple fallback
            return self._get_simple_fallback_scenario(category, difficulty)
    
    async def evaluate_response(
        self, 
        scenario: Dict[str, Any], 
        user_response: str
    ) -> Dict[str, Any]:
        """
        Evaluate user response using LM Studio with simple scoring
        
        Simple evaluation method that:
        1. Creates a basic evaluation prompt
        2. Sends to LM Studio for scoring
        3. Returns score and feedback
        """
        # Build simple evaluation prompt
        prompt = self._build_simple_evaluation_prompt(scenario, user_response)
        
        # Simple evaluation request
        payload = {
            "model": "local-model",  # Configure in LM Studio
            "messages": [
                {
                    "role": "system",
                    "content": EVALUATION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": DEFAULT_EVALUATION_TEMPERATURE,
            "max_tokens": DEFAULT_EVALUATION_MAX_TOKENS,
            "stream": False
        }
        
        try:
            # Make request to LM Studio
            response = await self._make_request("/v1/chat/completions", payload)
            evaluation_text = response["choices"][0]["message"]["content"]
            
            # Parse and return evaluation
            return self._parse_simple_evaluation_response(evaluation_text)
            
        except Exception as e:
            logger.error("Failed to evaluate response", error=str(e))
            # Return simple fallback evaluation
            return self._get_simple_fallback_evaluation()
    
    def _build_simple_scenario_prompt(self, category: str, difficulty: str) -> str:
        """
        Build prompt for simple scenario generation
        
        Uses the prompt template from prompts.py for easy modification.
        """
        return SCENARIO_USER_PROMPT_TEMPLATE.format(
            category=category, 
            difficulty=difficulty
        ).strip()
    
    def _build_simple_evaluation_prompt(self, scenario: Dict[str, Any], user_response: str) -> str:
        """
        Build prompt for simple response evaluation
        
        Uses the prompt template from prompts.py for easy modification.
        """
        return EVALUATION_USER_PROMPT_TEMPLATE.format(
            scenario_title=scenario.get('title', 'Healthcare Communication Scenario'),
            scenario_description=scenario.get('description', 'Practice communication scenario'),
            user_response=user_response
        ).strip()
    
    def _parse_simple_scenario_response(self, response_text: str, category: str, difficulty: str) -> Dict[str, Any]:
        """
        Parse LLM response for simple scenario generation
        """
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                scenario_data = json.loads(json_str)
                
                # Add metadata
                scenario_data.update({
                    "category": category,
                    "difficulty": difficulty
                })
                
                return scenario_data
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse scenario JSON, using fallback")
            return self._get_simple_fallback_scenario(category, difficulty)
    
    def _parse_simple_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response for simple evaluation
        
        Simple parsing that handles various response formats.
        Falls back gracefully if JSON parsing fails.
        """
        try:
            # Find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                evaluation_data = json.loads(json_str)
                
                # Ensure required fields with defaults
                score = evaluation_data.get("score", 7.0)
                feedback = evaluation_data.get("feedback", "Good communication effort.")
                
                # Validate score is in range
                if not isinstance(score, (int, float)) or score < 1 or score > 10:
                    score = 7.0
                
                return {
                    "score": float(score),
                    "feedback": str(feedback)
                }
            else:
                raise ValueError("No valid JSON found")
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning("Failed to parse evaluation JSON", error=str(e))
            return self._get_simple_fallback_evaluation()
    
    def _get_simple_fallback_scenario(self, category: str, difficulty: str) -> Dict[str, Any]:
        """
        Return a simple fallback scenario when LM Studio is unavailable
        
        Uses configuration from prompts.py for easy modification.
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
    
    def _get_simple_fallback_evaluation(self) -> Dict[str, Any]:
        """
        Return a simple fallback evaluation when LM Studio is unavailable
        
        Uses configuration from prompts.py for easy modification.
        """
        return {
            "score": FALLBACK_EVALUATION_SCORE,
            "feedback": FALLBACK_EVALUATION_FEEDBACK
        }
    
    def _build_scenario_prompt(self, category: str, difficulty: str, context: Optional[str]) -> str:
        """
        Build prompt for scenario generation
        """
        base_prompt = f"""
Create a healthcare communication scenario with the following requirements:

Category: {category}
Difficulty Level: {difficulty}
{f"Additional Context: {context}" if context else ""}

Please provide a structured response in the following JSON format:
{{
    "title": "Brief scenario title",
    "description": "Overview of the scenario",
    "patient_background": "Patient's medical history, demographics, and relevant background",
    "medical_context": "Current medical situation, diagnosis, treatment plan",
    "communication_challenge": "Specific communication challenge or goal for this scenario"
}}

Make the scenario realistic, educational, and appropriate for healthcare professionals to practice their communication skills.
"""
        return base_prompt.strip()
    
    def _build_evaluation_prompt(self, scenario: Dict[str, Any], user_response: str) -> str:
        """
        Build prompt for response evaluation
        """
        prompt = f"""
Evaluate the following healthcare communication response:

SCENARIO:
Title: {scenario.get('title', 'N/A')}
Context: {scenario.get('communication_challenge', 'N/A')}
Patient Background: {scenario.get('patient_background', 'N/A')}

USER RESPONSE:
{user_response}

Please evaluate this response on the following dimensions (scale 1-10):
1. Empathy: Shows understanding and compassion
2. Clarity: Clear, understandable communication
3. Professionalism: Maintains professional boundaries and demeanor
4. Medical Accuracy: Demonstrates appropriate medical knowledge

Provide your evaluation in the following JSON format:
{{
    "overall_score": 0.0,
    "empathy_score": 0.0,
    "clarity_score": 0.0,
    "professionalism_score": 0.0,
    "medical_accuracy_score": 0.0,
    "detailed_feedback": "Detailed explanation of strengths and areas for improvement",
    "improvement_suggestions": ["Specific suggestion 1", "Specific suggestion 2", "Specific suggestion 3"]
}}
"""
        return prompt.strip()
    
    def _parse_scenario_response(self, response_text: str, category: str, difficulty: str) -> Dict[str, Any]:
        """
        Parse LLM response for scenario generation
        """
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                scenario_data = json.loads(json_str)
                
                # Add metadata
                scenario_data.update({
                    "category": category,
                    "difficulty_level": difficulty
                })
                
                return scenario_data
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse scenario JSON, using fallback")
            return self._get_fallback_scenario(category, difficulty)
    
    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response for evaluation
        """
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                evaluation_data = json.loads(json_str)
                
                # Ensure all required fields exist
                required_fields = [
                    "overall_score", "empathy_score", "clarity_score", 
                    "professionalism_score", "medical_accuracy_score"
                ]
                
                for field in required_fields:
                    if field not in evaluation_data:
                        evaluation_data[field] = 5.0  # Default middle score
                
                return evaluation_data
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse evaluation JSON, using fallback")
            return self._get_fallback_evaluation()
    
    def _get_fallback_scenario(self, category: str, difficulty: str) -> Dict[str, Any]:
        """
        Return a fallback scenario when LM Studio is unavailable
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
            "difficulty_level": difficulty
        })
        
        return scenario
    
    def _get_fallback_evaluation(self) -> Dict[str, Any]:
        """
        Return a fallback evaluation when LM Studio is unavailable
        """
        return {
            "overall_score": 7.0,
            "empathy_score": 7.0,
            "clarity_score": 7.0,
            "professionalism_score": 7.0,
            "medical_accuracy_score": 7.0,
            "detailed_feedback": "Your response demonstrates good communication skills. Due to technical limitations, a detailed evaluation is not available at this time. Please try again later for comprehensive feedback.",
            "improvement_suggestions": [
                "Continue practicing active listening",
                "Focus on clear, concise communication",
                "Maintain professional empathy"
            ]
        }
