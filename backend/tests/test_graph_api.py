"""
Tests for the LangGraph API endpoints (graph structure, pipeline history).
"""


def test_graph_endpoint(client):
    """GET /autonomous/graph returns the graph topology."""
    response = client.get("/api/v1/autonomous/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "features" in data
    assert len(data["nodes"]) == 11
    assert any(n["id"] == "review" for n in data["nodes"])


def test_graph_has_parallel_feature(client):
    """Graph reports parallel_execution as a feature."""
    response = client.get("/api/v1/autonomous/graph")
    data = response.json()
    assert "parallel_execution" in data["features"]


def test_pipeline_history_empty(client):
    """Pipeline history is empty before any runs."""
    response = client.get("/api/v1/autonomous/pipeline-history")
    assert response.status_code == 200
    data = response.json()
    assert data["runs"] == []


def test_agent_status_active(client):
    """Agent status returns active with ollama backend."""
    response = client.get("/api/v1/autonomous/agent-status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["backend"] == "ollama"
    assert data["model"] == "mistral"
