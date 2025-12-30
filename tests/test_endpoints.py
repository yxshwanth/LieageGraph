import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_query_endpoint(client):
    response = client.post("/api/query", json={
        "query": "What feeds into revenue dashboard?",
        "depth": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "context_docs" in data
    assert "lineage_path" in data
    assert "confidence" in data
    assert isinstance(data["context_docs"], list)
    assert isinstance(data["lineage_path"], dict)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

