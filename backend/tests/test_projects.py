"""
Tests for project and autonomous endpoints.
"""


def test_list_projects_empty(client):
    res = client.get("/api/v1/autonomous/projects")
    assert res.status_code == 200
    assert res.json() == []


def test_get_project_not_found(client):
    res = client.get("/api/v1/autonomous/projects/nonexistent-id")
    assert res.status_code == 404


def test_agent_status(client):
    res = client.get("/api/v1/autonomous/agent-status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"


def test_clear_memory(client):
    res = client.post("/api/v1/autonomous/clear-memory")
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_create_film_validation_short_prompt(client):
    res = client.post("/api/v1/autonomous/create-film", json={
        "prompt": "hi",
        "style": "cinematic",
        "duration": 30,
    })
    assert res.status_code == 422


def test_create_film_validation_duration_range(client):
    res = client.post("/api/v1/autonomous/create-film", json={
        "prompt": "A beautiful sunset over the mountains",
        "style": "cinematic",
        "duration": 9999,
    })
    assert res.status_code == 422


def test_projects_crud_endpoint(client):
    res = client.post("/api/v1/projects/", json={
        "title": "Test Project",
        "description": "Test description",
        "format": "landscape",
    })
    assert res.status_code == 200
    assert res.json()["title"] == "Test Project"


def test_projects_list_endpoint(client):
    res = client.get("/api/v1/projects/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
