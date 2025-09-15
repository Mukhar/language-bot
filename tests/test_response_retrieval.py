"""
Simple test for response retrieval functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db
from app.models import Scenario, Response
import uuid


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_scenario(client):
    """Create a sample scenario for testing"""
    scenario_data = {
        "category": "general",
        "difficulty": "beginner"
    }
    
    response = client.post("/scenarios/generate", json=scenario_data)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def sample_response(client, sample_scenario):
    """Create a sample response for testing"""
    response_data = {
        "scenario_id": sample_scenario["id"],
        "response_text": "I would greet the patient warmly and ask how they are feeling today."
    }
    
    response = client.post("/responses/", json=response_data)
    assert response.status_code == 200
    return response.json()


def test_get_response_success(client, sample_response):
    """Test successful response retrieval"""
    response_id = sample_response["id"]
    
    response = client.get(f"/responses/{response_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == response_id
    assert data["response_text"] == sample_response["response_text"]
    assert data["scenario_id"] == sample_response["scenario_id"]


def test_get_response_not_found(client):
    """Test response retrieval with non-existent ID"""
    fake_id = str(uuid.uuid4())
    
    response = client.get(f"/responses/{fake_id}")
    
    assert response.status_code == 404
    assert "Response not found" in response.json()["detail"]


def test_get_response_invalid_id(client):
    """Test response retrieval with invalid ID"""
    response = client.get("/responses/")
    
    # Should get 404 because empty ID
    assert response.status_code == 404


def test_get_responses_for_scenario(client, sample_scenario, sample_response):
    """Test retrieving all responses for a scenario"""
    scenario_id = sample_scenario["id"]
    
    response = client.get(f"/responses/scenario/{scenario_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["scenario_id"] == scenario_id


def test_get_responses_for_nonexistent_scenario(client):
    """Test retrieving responses for non-existent scenario"""
    fake_scenario_id = str(uuid.uuid4())
    
    response = client.get(f"/responses/scenario/{fake_scenario_id}")
    
    assert response.status_code == 404
    assert "Scenario not found" in response.json()["detail"]


def test_get_responses_with_limit(client, sample_scenario):
    """Test retrieving responses with limit parameter"""
    scenario_id = sample_scenario["id"]
    
    response = client.get(f"/responses/scenario/{scenario_id}?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


if __name__ == "__main__":
    pytest.main([__file__])