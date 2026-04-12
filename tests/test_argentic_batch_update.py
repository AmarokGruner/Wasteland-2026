"""
Unit tests for the Argentic function `batch_update_units`.

These tests use an in‑memory SQLite database and the FastAPI TestClient
to invoke the function via the Hermes entry point.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the FastAPI app and the Argentic function we want to test
from app.main import app
from app.argentic_logic import batch_update_units
from app.models import Base, Province, Unit

# ----------------------------------------------------------------------
# Test database setup (in‑memory SQLite)
# ----------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

# Create all tables in the in‑memory DB
Base.metadata.create_all(bind=engine)


# ----------------------------------------------------------------------
# Dependency override for get_db (if the app uses a dependency)
# ----------------------------------------------------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override to the app (only needed if the app uses get_db)
app.dependency_overrides[app.get_db] = override_get_db  # type: ignore

client = TestClient(app)


# ----------------------------------------------------------------------
# Helper to seed a Province with sufficient MIPS
# ----------------------------------------------------------------------
def _seed_province(mips: int = 100) -> int:
    """Create a province with the given MIPS and return its ID."""
    db = TestingSessionLocal()
    province = Province(id=1, player_id=1, terrain="steppe", mips=mips)
    db.add(province)
    db.commit()
    db.close()
    return province.id


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_batch_update_units_success():
    """Happy‑path: recruit/train units successfully."""
    _seed_province(mips=100)

    response = client.post(
        "/execute_argentic",
        json={
            "function_name": "batch_update_units",
            "args": {"province_id": 1, "unit_type": "soldier", "count": 3},
        },
    )
    assert response.status_code == 200, "Expected successful response"
    data = response.json()
    assert data["status"] == "success"
    assert "unit_id" in data
    assert isinstance(data["unit_id"], int)


def test_batch_update_units_insufficient_mips():
    """Province does not have enough MIPS → 400 error."""
    _seed_province(mips=10)  # only 10 MIPS, need ~30 for 3 soldiers

    response = client.post(
        "/execute_argentic",
        json={
            "function_name": "batch_update_units",
            "args": {"province_id": 1, "unit_type": "soldier", "count": 3},
        },
    )
    assert response.status_code == 400, "Expected error for low MIPS"
    err = response.json()
    assert "INSUFFICIENT_MIPS" in err["detail"]


def test_batch_update_units_invalid_unit_type():
    """Unknown unit_type → 400 error."""
    _seed_province(mips=100)

    response = client.post(
        "/execute_argentic",
        json={
            "function_name": "batch_update_units",
            "args": {"province_id": 1, "unit_type": "dragon", "count": 1},
        },
    )
    assert response.status_code == 400, "Expected error for unsupported unit type"
    err = response.json()
    assert "Unsupported unit_type" in err["detail"]


def test_batch_update_units_missing_args():
    """Missing required arguments → 422 validation error."""
    response = client.post(
        "/execute_argentic",
        json={"function_name": "batch_update_units"},
    )
    assert response.status_code == 422, "Expected validation error for missing args"