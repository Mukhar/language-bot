import pytest
from unittest.mock import AsyncMock, patch
from app.services.lm_studio import LMStudioService
from app.schemas import ScenarioRequest


@pytest.fixture
def lm_client():
    """Create LM Studio service for testing"""
    return LMStudioService()


@pytest.mark.asyncio
async def test_lm_studio_scenario_generation(lm_client):
    """Test LM Studio scenario generation with mock"""
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"title": "Test Scenario", "description": "Test description"}'
            }
        }]
    }
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value.status_code = 200
        mock_post.return_value.__aenter__.return_value.raise_for_status = AsyncMock()
        
        result = await lm_client.generate_scenario(
            category="general",
            difficulty="beginner"
        )
        
        assert result["title"] == "Test Scenario"
        assert result["description"] == "Test description"
        assert result["category"] == "general"
        assert result["difficulty"] == "beginner"


@pytest.mark.asyncio
async def test_lm_studio_evaluation(lm_client):
    """Test LM Studio response evaluation with mock"""
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"score": 7.0, "feedback": "Good response with clear communication"}'
            }
        }]
    }
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value.status_code = 200
        mock_post.return_value.__aenter__.return_value.raise_for_status = AsyncMock()
        
        result = await lm_client.evaluate_response(
            scenario={"title": "Test scenario", "description": "Test scenario description"},
            user_response="Test response"
        )
        
        assert result["score"] == 7.0
        assert result["feedback"] == "Good response with clear communication"


@pytest.mark.asyncio
async def test_lm_studio_fallback_scenario(lm_client):
    """Test LM Studio fallback scenario when service is unavailable"""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.side_effect = Exception("Connection error")
        
        result = await lm_client.generate_scenario(
            category="emergency",
            difficulty="beginner"
        )
        
        # Should return fallback scenario
        assert result["title"] == "Emergency Communication"
        assert result["category"] == "emergency"
        assert result["difficulty"] == "beginner"


@pytest.mark.asyncio
async def test_lm_studio_fallback_evaluation(lm_client):
    """Test LM Studio fallback evaluation when service is unavailable"""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.side_effect = Exception("Connection error")
        
        result = await lm_client.evaluate_response(
            scenario={"title": "Test scenario", "description": "Test scenario description"},
            user_response="Test response"
        )
        
        # Should return fallback evaluation
        assert result["score"] == 7.0
        assert "AI evaluation is temporarily unavailable" in result["feedback"]


if __name__ == "__main__":
    pytest.main([__file__])
