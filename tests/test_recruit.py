import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the FastAPI app and DB dependencies
from app.main import app
from app.models import Base, Province, Player  # Adjust if your model names differ

# ----------------------------------------------------------------------
# Test database setup (in-memory SQLite)
# ----------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

# Create all tables in the in-memory DB
Base.metadata.create_all(bind=engine)


# ----------------------------------------------------------------------
# Dependency override for get_db
# ----------------------------------------------------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override to the app
app.dependency_overrides[app.get_db] = override_get_db  # type: ignore

client = TestClient(app)


# ----------------------------------------------------------------------
# Helper: create a minimal province + player for tests
# ----------------------------------------------------------------------
def _create_test_province():
    """Create a player and a province with default attributes."""
    db = next(TestingSessionLocal())
    # Create a player
    player = Player(id=1, username="testplayer", tech_level=1)
    # Create a province linked to that player
    province = Province(
        id=1,
        player_id=1,
        terrain="steppe",
        mips=100,  # enough MIPS for a simple recruit
    )
    db.add(player)
    db.add(province)
    db.commit()
    db.close()
    return province


# ----------------------------------------------------------------------
# Test cases
# ----------------------------------------------------------------------
def test_recruit_success():
    """Recruit new units – happy path."""
    _create_test_province()

    response = client.post(
        "/province/1/military/recruit",
        json={"unit_type": "soldier", "count": 3},
    )
    assert response.status_code == 200, "Expected 200 OK"
    data = response.json()
    assert data["success"] is True, "Recruit should report success"
    assert "unit_id" in data, "Response must contain unit_id"
    assert isinstance(data["unit_id"], int), "unit_id should be integer"


def test_recruit_invalid_unit_type():
    """Recruit with an unknown unit_type should fail."""
    _create_test_province()

    response = client.post(
        "/province/1/military/recruit",
        json={"unit_type": "dragon", "count": 1},
    )
    assert response.status_code == 400, "Expected 400 Bad Request for unknown unit"


def test_recruit_negative_count():
    """Negative count should be rejected by the API validation."""
    _create_test_province()

    response = client.post(
        "/province/1/military/recruit",
        json={"unit_type": "soldier", "count": -5},
    )
    # FastAPI validation should return 422 Unprocessable Entity
    assert response.status_code == 422, "Expected validation error for negative count"


def test_recruit_insufficient_mips(caplog):
    """Recruit when the province does not have enough MIPS should fail."""
    db = next(TestingSessionLocal())
    province = Province(id=1, player_id=1, terrain="steppe", mips=10)
    db.add(province)
    db.commit()
    db.close()

    response = client.post(
        "/province/1/military/recruit",
        json={"unit_type": "soldier", "count": 1},
    )
    assert response.status_code == 400, "Expected error when MIPS are insufficient"
    # Optionally check the error message contains the MIPS check
    # assert "INSUFFICIENT_MIPS" in response.text