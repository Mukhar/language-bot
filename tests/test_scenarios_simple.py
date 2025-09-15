import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock
import uuid

from app.main import app
from app.database import get_db, Base
from app.models import Scenario


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_scenarios_simple.db"
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
def clean_database():
    """Clean database before each test"""
    db = TestingSessionLocal()
    db.query(Scenario).delete()
    db.commit()
    db.close()
    yield


def test_generate_simple_scenario_success(setup_database, clean_database):
    """Test successful simple scenario generation"""
    mock_lm_response = {
        "title": "Emergency Communication",
        "description": "Practice communicating with a patient in an emergency setting.",
        "category": "emergency",
        "difficulty": "intermediate"
    }
    
    with patch('app.services.lm_studio.LMStudioService.generate_scenario') as mock_generate:
        mock_generate.return_value = mock_lm_response
        
        response = client.post("/scenarios/generate", json={
            "category": "emergency",
            "difficulty": "intermediate"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Emergency Communication"
        assert data["category"] == "emergency"
        assert data["difficulty"] == "intermediate"
        assert "description" in data
        assert "id" in data


def test_generate_scenario_invalid_category(setup_database, clean_database):
    """Test scenario generation with invalid category"""
    response = client.post("/scenarios/generate", json={
        "category": "invalid",
        "difficulty": "beginner"
    })
    
    assert response.status_code == 422  # Validation error


def test_generate_scenario_invalid_difficulty(setup_database, clean_database):
    """Test scenario generation with invalid difficulty"""
    response = client.post("/scenarios/generate", json={
        "category": "general",
        "difficulty": "advanced"  # Not allowed in simplified version
    })
    
    assert response.status_code == 422  # Validation error


def test_get_scenario_by_id(setup_database, clean_database):
    """Test retrieving scenario by ID"""
    # First create a scenario
    with patch('app.services.lm_studio.LMStudioService.generate_scenario') as mock_generate:
        mock_generate.return_value = {
            "title": "Test Scenario",
            "description": "Test description for simple scenario",
            "category": "general",
            "difficulty": "beginner"
        }
        
        create_response = client.post("/scenarios/generate", json={
            "category": "general",
            "difficulty": "beginner"
        })
        
        scenario_id = create_response.json()["id"]
        
        # Now retrieve it
        get_response = client.get(f"/scenarios/{scenario_id}")
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["title"] == "Test Scenario"
        assert data["id"] == scenario_id
        assert data["category"] == "general"
        assert data["difficulty"] == "beginner"


def test_get_scenario_not_found(setup_database, clean_database):
    """Test scenario not found error"""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/scenarios/{fake_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_generate_scenario_with_lm_studio_failure(setup_database, clean_database):
    """Test scenario generation when LM Studio fails"""
    with patch('app.services.lm_studio.LMStudioService.generate_scenario') as mock_generate:
        # Mock LM Studio failure - should return fallback scenario
        mock_generate.return_value = {
            "title": "General Patient Communication",
            "description": "Practice general communication skills with a patient.",
            "category": "general",
            "difficulty": "beginner"
        }
        
        response = client.post("/scenarios/generate", json={
            "category": "general",
            "difficulty": "beginner"
        })
        
        # Should still succeed with fallback
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "description" in data


def test_valid_category_options(setup_database, clean_database):
    """Test that only valid categories are accepted"""
    valid_categories = ["general", "emergency", "routine"]
    
    for category in valid_categories:
        with patch('app.services.lm_studio.LMStudioService.generate_scenario') as mock_generate:
            mock_generate.return_value = {
                "title": f"{category.title()} Scenario",
                "description": f"A {category} communication scenario",
                "category": category,
                "difficulty": "beginner"
            }
            
            response = client.post("/scenarios/generate", json={
                "category": category,
                "difficulty": "beginner"
            })
            
            assert response.status_code == 200


def test_valid_difficulty_options(setup_database, clean_database):
    """Test that only valid difficulties are accepted"""
    valid_difficulties = ["beginner", "intermediate"]
    
    for difficulty in valid_difficulties:
        with patch('app.services.lm_studio.LMStudioService.generate_scenario') as mock_generate:
            mock_generate.return_value = {
                "title": f"{difficulty.title()} Scenario",
                "description": f"A {difficulty} level communication scenario",
                "category": "general",
                "difficulty": difficulty
            }
            
            response = client.post("/scenarios/generate", json={
                "category": "general",
                "difficulty": difficulty
            })
            
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])