import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import uuid

from app.main import app
from app.database import get_db, Base
from app.models import Scenario, Response, Evaluation


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_evaluations.db"
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
def sample_response(setup_database):
    """Create a sample scenario and response for testing evaluations"""
    db = TestingSessionLocal()
    
    # Create scenario
    scenario = Scenario(
        id=str(uuid.uuid4()),
        title="Test Evaluation Scenario",
        description="A scenario for testing evaluations",
        patient_background="Test patient background",
        medical_context="Test medical context",
        communication_challenge="Test communication challenge",
        category="general",
        difficulty_level="beginner"
    )
    db.add(scenario)
    
    # Create response
    response = Response(
        id=str(uuid.uuid4()),
        scenario_id=scenario.id,
        response_text="This is a test response that will be evaluated for communication effectiveness."
    )
    db.add(response)
    db.commit()
    
    response_id = response.id
    scenario_data = {
        "description": scenario.description,
        "patient_background": scenario.patient_background,
        "medical_context": scenario.medical_context,
        "communication_challenge": scenario.communication_challenge
    }
    
    db.close()
    return response_id, scenario_data


def test_create_evaluation_success(sample_response):
    """Test successful evaluation creation"""
    response_id, scenario_data = sample_response
    
    mock_evaluation = {
        "score": 85,
        "feedback": "Good communication skills demonstrated with clear explanation and empathy.",
        "improvement_suggestions": [
            "Consider using more accessible language",
            "Provide more specific timeframes"
        ]
    }
    
    with patch('app.services.lm_studio.LMStudioService.evaluate_response') as mock_evaluate:
        mock_evaluate.return_value = mock_evaluation
        
        response = client.post(f"/api/v1/evaluations/{response_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["response_id"] == response_id
        assert data["score"] == 85
        assert "Good communication skills" in data["feedback"]
        assert len(data["improvement_suggestions"]) == 2


def test_create_evaluation_response_not_found():
    """Test evaluation creation with nonexistent response"""
    nonexistent_id = str(uuid.uuid4())
    
    response = client.post(f"/api/v1/evaluations/{nonexistent_id}")
    assert response.status_code == 404
    assert "Response not found" in response.json()["detail"]


def test_get_evaluation_by_id(sample_response):
    """Test retrieving evaluation by ID"""
    response_id, scenario_data = sample_response
    
    mock_evaluation = {
        "score": 78,
        "feedback": "Adequate response with room for improvement in empathy and clarity.",
        "improvement_suggestions": ["Show more empathy", "Be more specific"]
    }
    
    with patch('app.services.lm_studio.LMStudioService.evaluate_response') as mock_evaluate:
        mock_evaluate.return_value = mock_evaluation
        
        # Create evaluation
        create_response = client.post(f"/api/v1/evaluations/{response_id}")
        evaluation_id = create_response.json()["id"]
        
        # Retrieve evaluation
        get_response = client.get(f"/api/v1/evaluations/{evaluation_id}")
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["id"] == evaluation_id
        assert data["score"] == 78
        assert "Adequate response" in data["feedback"]


def test_get_evaluation_not_found():
    """Test retrieving nonexistent evaluation"""
    nonexistent_id = str(uuid.uuid4())
    
    response = client.get(f"/api/v1/evaluations/{nonexistent_id}")
    assert response.status_code == 404
    assert "Evaluation not found" in response.json()["detail"]


def test_list_evaluations_empty():
    """Test listing evaluations when none exist"""
    response = client.get("/api/v1/evaluations/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_evaluations_with_data(sample_response):
    """Test listing evaluations with existing data"""
    response_id, scenario_data = sample_response
    
    mock_evaluation = {
        "score": 92,
        "feedback": "Excellent communication with clear structure and appropriate empathy.",
        "improvement_suggestions": ["Continue current approach"]
    }
    
    with patch('app.services.lm_studio.LMStudioService.evaluate_response') as mock_evaluate:
        mock_evaluate.return_value = mock_evaluation
        
        # Create evaluation
        create_response = client.post(f"/api/v1/evaluations/{response_id}")
        created_id = create_response.json()["id"]
        
        # List evaluations
        list_response = client.get("/api/v1/evaluations/")
        assert list_response.status_code == 200
        
        data = list_response.json()
        assert isinstance(data, list)
        
        # Check if our created evaluation is in the list
        evaluation_ids = [e["id"] for e in data]
        assert created_id in evaluation_ids


def test_get_evaluation_by_response_id(sample_response):
    """Test retrieving evaluation by response ID"""
    response_id, scenario_data = sample_response
    
    mock_evaluation = {
        "score": 88,
        "feedback": "Strong response demonstrating good clinical communication principles.",
        "improvement_suggestions": ["Consider patient's emotional state more"]
    }
    
    with patch('app.services.lm_studio.LMStudioService.evaluate_response') as mock_evaluate:
        mock_evaluate.return_value = mock_evaluation
        
        # Create evaluation
        client.post(f"/api/v1/evaluations/{response_id}")
        
        # Get evaluation by response ID
        response = client.get(f"/api/v1/evaluations/response/{response_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["response_id"] == response_id
        assert data["score"] == 88
        assert "Strong response" in data["feedback"]


def test_get_evaluation_by_response_id_not_found():
    """Test retrieving evaluation for response that has no evaluation"""
    nonexistent_id = str(uuid.uuid4())
    
    response = client.get(f"/api/v1/evaluations/response/{nonexistent_id}")
    assert response.status_code == 404


def test_evaluation_score_range(sample_response):
    """Test evaluation score validation"""
    response_id, scenario_data = sample_response
    
    # Test with score within valid range
    mock_evaluation = {
        "score": 95,
        "feedback": "Outstanding performance",
        "improvement_suggestions": []
    }
    
    with patch('app.services.lm_studio.LMStudioService.evaluate_response') as mock_evaluate:
        mock_evaluate.return_value = mock_evaluation
        
        response = client.post(f"/api/v1/evaluations/{response_id}")
        assert response.status_code == 200
        assert response.json()["score"] == 95


def test_evaluation_with_lm_studio_error(sample_response):
    """Test evaluation creation when LM Studio service fails"""
    response_id, scenario_data = sample_response
    
    # Mock LM Studio service to return fallback evaluation
    fallback_evaluation = {
        "score": 75,
        "feedback": "Unable to connect to LM Studio for detailed evaluation. Please try again later.",
        "improvement_suggestions": ["Ensure clear communication", "Show empathy"]
    }
    
    with patch('app.services.lm_studio.LMStudioService.evaluate_response') as mock_evaluate:
        mock_evaluate.return_value = fallback_evaluation
        
        response = client.post(f"/api/v1/evaluations/{response_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["score"] == 75
        assert "Unable to connect to LM Studio" in data["feedback"]


def test_multiple_evaluations_same_response(sample_response):
    """Test creating multiple evaluations for the same response"""
    response_id, scenario_data = sample_response
    
    mock_evaluation = {
        "score": 80,
        "feedback": "Good response",
        "improvement_suggestions": ["Be more specific"]
    }
    
    with patch('app.services.lm_studio.LMStudioService.evaluate_response') as mock_evaluate:
        mock_evaluate.return_value = mock_evaluation
        
        # Create first evaluation
        first_response = client.post(f"/api/v1/evaluations/{response_id}")
        assert first_response.status_code == 200
        
        # Try to create second evaluation for same response
        second_response = client.post(f"/api/v1/evaluations/{response_id}")
        # This might return 409 (conflict) if only one evaluation per response is allowed
        # Or 200 if multiple evaluations are allowed
        # Implementation depends on business requirements
        assert second_response.status_code in [200, 409]


if __name__ == "__main__":
    pytest.main([__file__])
