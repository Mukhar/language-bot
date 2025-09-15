import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Scenario, Response
import uuid


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_models.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_test_db():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_test_db):
    """Create a database session for testing"""
    session = TestingSessionLocal()
    yield session
    # Clean up after each test
    session.query(Response).delete()
    session.query(Scenario).delete()
    session.commit()
    session.close()


def test_scenario_model_creation(db_session):
    """Test creating a simple scenario model"""
    scenario = Scenario(
        id=str(uuid.uuid4()),
        title="Test Scenario",
        description="Test scenario description for basic communication practice",
        category="general",
        difficulty="beginner"
    )
    
    db_session.add(scenario)
    db_session.commit()
    
    # Retrieve and verify
    retrieved_scenario = db_session.query(Scenario).filter(Scenario.title == "Test Scenario").first()
    assert retrieved_scenario is not None
    assert retrieved_scenario.category == "general"
    assert retrieved_scenario.difficulty == "beginner"
    assert retrieved_scenario.description == "Test scenario description for basic communication practice"


def test_response_model_creation(db_session):
    """Test creating a simple response model"""
    # Create scenario first
    scenario = Scenario(
        id=str(uuid.uuid4()),
        title="Test Scenario for Response",
        description="Test scenario for response testing",
        category="routine",
        difficulty="intermediate"
    )
    db_session.add(scenario)
    db_session.commit()
    
    # Create response without evaluation initially
    response = Response(
        id=str(uuid.uuid4()),
        scenario_id=scenario.id,
        response_text="This is a test response to the scenario showing good communication skills."
    )
    
    db_session.add(response)
    db_session.commit()
    
    # Retrieve and verify
    retrieved_response = db_session.query(Response).filter(Response.scenario_id == scenario.id).first()
    assert retrieved_response is not None
    assert retrieved_response.response_text == "This is a test response to the scenario showing good communication skills."
    assert retrieved_response.scenario_id == scenario.id
    assert retrieved_response.score is None  # Not evaluated yet
    assert retrieved_response.feedback is None  # Not evaluated yet


def test_response_with_evaluation(db_session):
    """Test response model with embedded evaluation"""
    # Create scenario first
    scenario = Scenario(
        id=str(uuid.uuid4()),
        title="Evaluation Test Scenario",
        description="Test scenario for evaluation testing",
        category="emergency",
        difficulty="beginner"
    )
    db_session.add(scenario)
    db_session.commit()
    
    # Create response with evaluation
    response = Response(
        id=str(uuid.uuid4()),
        scenario_id=scenario.id,
        response_text="Test response for evaluation",
        score=8.5,
        feedback="Good communication with clear empathy and professional tone. Consider being more specific about next steps."
    )
    
    db_session.add(response)
    db_session.commit()
    
    # Retrieve and verify
    retrieved_response = db_session.query(Response).filter(Response.score == 8.5).first()
    assert retrieved_response is not None
    assert retrieved_response.score == 8.5
    assert "Good communication" in retrieved_response.feedback
    assert retrieved_response.response_text == "Test response for evaluation"


def test_scenario_categories_and_difficulties(db_session):
    """Test different scenario categories and difficulties"""
    test_scenarios = [
        ("general", "beginner", "Basic patient interaction"),
        ("emergency", "intermediate", "Emergency department communication"),
        ("routine", "beginner", "Regular check-up discussion"),
    ]
    
    for category, difficulty, description in test_scenarios:
        scenario = Scenario(
            id=str(uuid.uuid4()),
            title=f"{category.title()} {difficulty.title()} Scenario",
            description=description,
            category=category,
            difficulty=difficulty
        )
        db_session.add(scenario)
    
    db_session.commit()
    
    # Test querying by category
    general_scenarios = db_session.query(Scenario).filter(Scenario.category == "general").all()
    assert len(general_scenarios) == 1
    
    # Test querying by difficulty
    beginner_scenarios = db_session.query(Scenario).filter(Scenario.difficulty == "beginner").all()
    assert len(beginner_scenarios) == 2


def test_response_evaluation_workflow(db_session):
    """Test the workflow of creating response and adding evaluation"""
    # Create scenario
    scenario = Scenario(
        id=str(uuid.uuid4()),
        title="Workflow Test Scenario",
        description="Testing the response evaluation workflow",
        category="general",
        difficulty="beginner"
    )
    db_session.add(scenario)
    db_session.commit()
    
    # Step 1: Create response without evaluation
    response = Response(
        id=str(uuid.uuid4()),
        scenario_id=scenario.id,
        response_text="Initial response without evaluation"
    )
    db_session.add(response)
    db_session.commit()
    
    # Verify initial state
    assert response.score is None
    assert response.feedback is None
    
    # Step 2: Update evaluation in existing response
    db_session.query(Response).filter(Response.id == response.id).update({
        "score": 7.0,
        "feedback": "Adequate response. Shows understanding but could be more empathetic."
    })
    db_session.commit()
    
    # Verify evaluation was added
    retrieved_response = db_session.query(Response).filter(Response.id == response.id).first()
    assert retrieved_response.score == 7.0
    assert "Adequate response" in retrieved_response.feedback


if __name__ == "__main__":
    pytest.main([__file__])
