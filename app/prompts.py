"""
Simple prompt templates for the healthcare communication bot.

This file contains all prompts used by the LM Studio service.
You can easily modify these prompts to change the AI's behavior.
"""

# Scenario Generation Prompts
SCENARIO_SYSTEM_PROMPT = "You are a healthcare communication trainer. Generate simple practice scenarios."

SCENARIO_USER_PROMPT_TEMPLATE = """
Generate a healthcare communication scenario for practice.

Requirements:
- Category: {category}
- Difficulty: {difficulty}
- Keep it simple and realistic
- Focus on communication skills practice

Respond with JSON format only:
{{
    "title": "Clear, brief scenario title",
    "description": "Simple scenario description for healthcare communication practice"
}}
"""

# Evaluation Prompts
EVALUATION_SYSTEM_PROMPT = "You are a healthcare communication expert. Evaluate responses with constructive feedback."

EVALUATION_USER_PROMPT_TEMPLATE = """
Evaluate this healthcare communication response on a scale of 1-10.

SCENARIO:
{scenario_title}
{scenario_description}

USER'S RESPONSE:
{user_response}

Rate the response and give brief feedback. Respond with JSON only:
{{
    "score": 7.5,
    "feedback": "Brief feedback explaining the score and suggestions for improvement"
}}

Consider:
- Communication clarity
- Professional tone
- Empathy and understanding
- Appropriateness for healthcare setting
"""

# Fallback responses
FALLBACK_SCENARIO_TITLE = "General Healthcare Communication"
FALLBACK_SCENARIO_DESCRIPTION = "Practice professional communication with a patient in a healthcare setting."

FALLBACK_EVALUATION_SCORE = 7.0
FALLBACK_EVALUATION_FEEDBACK = "Your response shows good communication effort. AI evaluation is temporarily unavailable, but your response has been saved for review."

# LM Studio Configuration
DEFAULT_SCENARIO_TEMPERATURE = 0.7
DEFAULT_SCENARIO_MAX_TOKENS = 300

DEFAULT_EVALUATION_TEMPERATURE = 0.3
DEFAULT_EVALUATION_MAX_TOKENS = 200