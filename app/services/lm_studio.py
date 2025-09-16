import httpx
import json
import os
import time
from typing import Dict, Any, Optional
from ..config import get_settings
from ..prompts import (
    SCENARIO_SYSTEM_PROMPT,
    EVALUATION_SYSTEM_PROMPT,
    DEFAULT_SCENARIO_TEMPERATURE,
    DEFAULT_SCENARIO_MAX_TOKENS,
    DEFAULT_EVALUATION_TEMPERATURE,
    DEFAULT_EVALUATION_MAX_TOKENS
)
from .fallbacks import (
    get_simple_fallback_scenario,
    get_simple_fallback_evaluation,
    get_fallback_scenario,
    get_fallback_evaluation
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
        
        Enhanced with detailed logging for monitoring and debugging.
        """
        start_time = time.time()
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(
            "Making request to LM Studio",
            url=url,
            endpoint=endpoint,
            timeout=self.timeout,
            has_api_key=bool(self.api_key),
            payload_size=len(str(payload))
        )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                elapsed_time = time.time() - start_time
                
                logger.debug(
                    "LM Studio response received",
                    status_code=response.status_code,
                    response_time_seconds=round(elapsed_time, 2),
                    response_size=len(response.text) if hasattr(response, 'text') else 0
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            elapsed_time = time.time() - start_time
            logger.error(
                "LM Studio request timeout",
                url=url,
                timeout=self.timeout,
                elapsed_time_seconds=round(elapsed_time, 2)
            )
            raise LMStudioError("Request to LM Studio timed out")
            
        except httpx.HTTPStatusError as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "LM Studio HTTP error",
                status_code=e.response.status_code,
                url=url,
                elapsed_time_seconds=round(elapsed_time, 2),
                response_text=e.response.text[:200] if hasattr(e.response, 'text') else "N/A"
            )
            raise LMStudioError(f"LM Studio API error: {e.response.status_code}")
            
        except httpx.RequestError as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "LM Studio connection error",
                error=str(e),
                url=url,
                elapsed_time_seconds=round(elapsed_time, 2)
            )
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
        Enhanced with detailed logging for monitoring and debugging.
        """
        start_time = time.time()
        
        logger.info(
            "Starting scenario generation",
            category=category,
            difficulty=difficulty,
            lm_studio_url=self.base_url
        )
        
        # Build scenario prompt
        logger.debug("Building scenario generation prompt", category=category, difficulty=difficulty)
        prompt = self._build_scenario_prompt(category, difficulty, None)
        
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
        
        logger.debug(
            "Sending request to LM Studio",
            temperature=DEFAULT_SCENARIO_TEMPERATURE,
            max_tokens=DEFAULT_SCENARIO_MAX_TOKENS,
            prompt_length=len(prompt)
        )
        
        try:
            # Make request to LM Studio
            response = await self._make_request("/v1/chat/completions", payload)
            
            elapsed_time = time.time() - start_time
            scenario_text = response["choices"][0]["message"]["content"]
            
            logger.info(
                "LM Studio response received",
                response_time_seconds=round(elapsed_time, 2),
                response_length=len(scenario_text),
                category=category,
                difficulty=difficulty
            )
            
            # Parse the response
            parsed_scenario = self._parse_scenario_response(scenario_text, category, difficulty)
            
            logger.info(
                "Scenario generation completed successfully",
                total_time_seconds=round(time.time() - start_time, 2),
                title=parsed_scenario.get("title", "N/A")[:50],
                category=category,
                difficulty=difficulty,
                used_fallback=False
            )
            
            return parsed_scenario
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Failed to generate scenario from LM Studio",
                error=str(e),
                error_type=type(e).__name__,
                category=category,
                difficulty=difficulty,
                elapsed_time_seconds=round(elapsed_time, 2),
                fallback_used=True
            )
            
            # Return simple fallback
            fallback_scenario = get_simple_fallback_scenario(category, difficulty)
            
            logger.info(
                "Using fallback scenario",
                total_time_seconds=round(time.time() - start_time, 2),
                title=fallback_scenario.get("title", "N/A"),
                category=category,
                difficulty=difficulty,
                used_fallback=True
            )
            
            return fallback_scenario
    
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
        prompt = self._build_evaluation_prompt(scenario, user_response)
        
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
            return self._parse_evaluation_response(evaluation_text)
            
        except Exception as e:
            logger.error("Failed to evaluate response", error=str(e))
            # Return simple fallback evaluation
            return get_simple_fallback_evaluation()
    
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
    "score": 8.0,
    "empathy_score": 8.0,
    "clarity_score": 8.0,
    "professionalism_score": 8.0,
    "medical_accuracy_score": 8.0,
    "feedback": "Detailed explanation of strengths and areas for improvement",
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
                    "difficulty": difficulty
                })
                
                return scenario_data
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse scenario JSON, using fallback")
            return get_simple_fallback_scenario(category, difficulty)
    
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
                    "score", "empathy_score", "clarity_score", 
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
            return get_simple_fallback_evaluation()
