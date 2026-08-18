import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Source

client = TestClient(app)


def test_list_jobs():
    """Test listing jobs endpoint."""
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_sources():
    """Test listing sources endpoint."""
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_jobs():
    """Test job search endpoint."""
    response = client.get("/api/jobs/search?q=python")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_ingestion_runs():
    """Test listing ingestion runs."""
    response = client.get("/api/ingestion/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
