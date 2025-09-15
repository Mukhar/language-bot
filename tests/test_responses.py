import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import uuid

from app.main import app
from app.database import get_db, Base
from app.models import Scenario, Response


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_responses.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="session")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_scenario(setup_database):
    """Create a sample scenario for testing responses"""
    db = TestingSessionLocal()
    scenario = Scenario(
        id=str(uuid.uuid4()),
        title="Test Response Scenario",
        description="A scenario for testing responses",
        patient_background="Test patient background",
        medical_context="Test medical context",
        communication_challenge="Test communication challenge",
        category="general",
        difficulty_level="beginner"
    )
    db.add(scenario)
    db.commit()
    scenario_id = scenario.id
    db.close()
    return scenario_id


def test_submit_response_success(sample_scenario):
    """Test successful response submission"""
    response_data = {
        "scenario_id": sample_scenario,
        "response_text": "This is a comprehensive response that demonstrates clear communication skills and empathy towards the patient."
    }
    
    response = client.post("/api/v1/responses/", json=response_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["scenario_id"] == sample_scenario
    assert data["response_text"] == response_data["response_text"]
    assert "created_at" in data


def test_submit_response_with_user_id(sample_scenario):
    """Test response submission with user ID"""
    user_id = str(uuid.uuid4())
    response_data = {
        "scenario_id": sample_scenario,
        "user_id": user_id,
        "response_text": "This is a response with a user ID attached for tracking purposes."
    }
    
    response = client.post("/api/v1/responses/", json=response_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == user_id


def test_submit_response_validation_errors(sample_scenario):
    """Test response submission validation errors"""
    # Test too short response
    response_data = {
        "scenario_id": sample_scenario,
        "response_text": "Short"
    }
    
    response = client.post("/api/v1/responses/", json=response_data)
    assert response.status_code == 422
    
    # Test missing scenario_id
    response_data = {
        "response_text": "This is a valid length response but missing scenario ID."
    }
    
    response = client.post("/api/v1/responses/", json=response_data)
    assert response.status_code == 422
    
    # Test missing response_text
    response_data = {
        "scenario_id": sample_scenario
    }
    
    response = client.post("/api/v1/responses/", json=response_data)
    assert response.status_code == 422


def test_submit_response_nonexistent_scenario():
    """Test response submission with nonexistent scenario"""
    nonexistent_id = str(uuid.uuid4())
    response_data = {
        "scenario_id": nonexistent_id,
        "response_text": "This is a response to a scenario that doesn't exist in the database."
    }
    
    response = client.post("/api/v1/responses/", json=response_data)
    assert response.status_code == 404
    assert "Scenario not found" in response.json()["detail"]


def test_get_response_by_id(sample_scenario):
    """Test retrieving response by ID"""
    # First create a response
    response_data = {
        "scenario_id": sample_scenario,
        "response_text": "This is a response that we will retrieve by its ID later."
    }
    
    create_response = client.post("/api/v1/responses/", json=response_data)
    response_id = create_response.json()["id"]
    
    # Now retrieve it
    get_response = client.get(f"/api/v1/responses/{response_id}")
    assert get_response.status_code == 200
    
    data = get_response.json()
    assert data["id"] == response_id
    assert data["response_text"] == response_data["response_text"]


def test_get_response_not_found():
    """Test retrieving nonexistent response"""
    nonexistent_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/responses/{nonexistent_id}")
    assert response.status_code == 404
    assert "Response not found" in response.json()["detail"]


def test_list_responses_empty():
    """Test listing responses when none exist"""
    response = client.get("/api/v1/responses/")
    assert response.status_code == 200
    # Note: There might be responses from other tests, so we just check it's a list
    assert isinstance(response.json(), list)


def test_list_responses_with_data(sample_scenario):
    """Test listing responses with existing data"""
    # Create a response
    response_data = {
        "scenario_id": sample_scenario,
        "response_text": "This is a response for the listing test case to verify API functionality."
    }
    
    create_response = client.post("/api/v1/responses/", json=response_data)
    created_id = create_response.json()["id"]
    
    # List responses
    list_response = client.get("/api/v1/responses/")
    assert list_response.status_code == 200
    
    data = list_response.json()
    assert isinstance(data, list)
    
    # Check if our created response is in the list
    response_ids = [r["id"] for r in data]
    assert created_id in response_ids


def test_list_responses_by_scenario(sample_scenario):
    """Test listing responses filtered by scenario"""
    # Create multiple responses for the scenario
    for i in range(3):
        response_data = {
            "scenario_id": sample_scenario,
            "response_text": f"This is response number {i+1} for the scenario filtering test case."
        }
        client.post("/api/v1/responses/", json=response_data)
    
    # List responses for the specific scenario
    response = client.get(f"/api/v1/responses/?scenario_id={sample_scenario}")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    
    # Verify all responses belong to the same scenario
    for response_item in data:
        assert response_item["scenario_id"] == sample_scenario


def test_response_text_length_validation(sample_scenario):
    """Test response text length validation"""
    # Test minimum length (should pass)
    valid_response = {
        "scenario_id": sample_scenario,
        "response_text": "This response meets the minimum character length requirement for validation."
    }
    
    response = client.post("/api/v1/responses/", json=valid_response)
    assert response.status_code == 200
    
    # Test maximum length (create a very long response)
    long_text = "A" * 5001  # Assuming max length is 5000
    long_response = {
        "scenario_id": sample_scenario,
        "response_text": long_text
    }
    
    response = client.post("/api/v1/responses/", json=long_response)
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
