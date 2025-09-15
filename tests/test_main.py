import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from app.main import app
from app.database import get_db, Base


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

# Create test client
client = TestClient(app)


@pytest.fixture(scope="session")
def setup_database():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


def test_root_endpoint(setup_database):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_health_endpoint(setup_database):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_health_endpoint(setup_database):
    """Test the API health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_generate_scenario_endpoint(setup_database):
    """Test scenario generation endpoint"""
    scenario_request = {
        "category": "emergency",
        "difficulty_level": "intermediate",
        "context": "Test scenario generation"
    }
    
    response = client.post("/api/v1/scenarios/generate", json=scenario_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["category"] == "emergency"
    assert data["difficulty_level"] == "intermediate"
    assert "title" in data
    assert "description" in data


def test_get_scenario_categories(setup_database):
    """Test getting scenario categories"""
    response = client.get("/api/v1/scenarios/categories/list")
    assert response.status_code == 200
    
    data = response.json()
    assert "categories" in data
    assert "difficulty_levels" in data
    assert "beginner" in data["difficulty_levels"]


def test_scenario_not_found(setup_database):
    """Test scenario not found"""
    response = client.get("/api/v1/scenarios/nonexistent-id")
    assert response.status_code == 404


def test_submit_response(setup_database):
    """Test submitting a response"""
    # First create a scenario
    scenario_request = {
        "category": "general",
        "difficulty_level": "beginner"
    }
    
    scenario_response = client.post("/api/v1/scenarios/generate", json=scenario_request)
    assert scenario_response.status_code == 200
    scenario_id = scenario_response.json()["id"]
    
    # Submit a response
    response_request = {
        "scenario_id": scenario_id,
        "response_text": "This is a test response that meets the minimum length requirement."
    }
    
    response = client.post("/api/v1/responses/", json=response_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["scenario_id"] == scenario_id
    assert data["response_text"] == response_request["response_text"]


def test_response_validation(setup_database):
    """Test response validation"""
    # Test with too short response
    response_request = {
        "scenario_id": "test-id",
        "response_text": "short"
    }
    
    response = client.post("/api/v1/responses/", json=response_request)
    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__])
