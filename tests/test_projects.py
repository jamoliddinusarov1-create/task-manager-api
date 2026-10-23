from fastapi.testclient import TestClient


def test_create_and_get_project(client: TestClient, user1_headers: dict):
    """Test creating a project and retrieving its details."""
    payload = {"name": "Backend Development", "description": "FastAPI Project"}
    res = client.post("/api/v1/projects", json=payload, headers=user1_headers)
    assert res.status_code == 201
    project_data = res.json()
    assert project_data["name"] == "Backend Development"
    assert project_data["description"] == "FastAPI Project"

    # Get details
    project_id = project_data["id"]
    get_res = client.get(f"/api/v1/projects/{project_id}", headers=user1_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id


def test_projects_isolation_between_users(
    client: TestClient,
    user1_headers: dict,
    user2_headers: dict
):
    """
    Business Rule & Exam Defense:
    User 1 creates a project. User 2 must NOT see or access it.
    Accessing another user's project ID returns 404 Not Found.
    """
    # User 1 creates project
    p1 = client.post(
        "/api/v1/projects",
        json={"name": "User 1 Secret Project"},
        headers=user1_headers
    ).json()

    # User 2 lists projects -> should be empty
    u2_list = client.get("/api/v1/projects", headers=user2_headers).json()
    assert len(u2_list) == 0

    # User 2 tries to GET User 1's project directly by ID -> returns 404
    u2_get = client.get(f"/api/v1/projects/{p1['id']}", headers=user2_headers)
    assert u2_get.status_code == 404

    # User 2 tries to DELETE User 1's project -> returns 404
    u2_del = client.delete(f"/api/v1/projects/{p1['id']}", headers=user2_headers)
    assert u2_del.status_code == 404


def test_delete_empty_project_success(client: TestClient, user1_headers: dict):
    """Test that an empty project can be safely deleted."""
    project = client.post(
        "/api/v1/projects",
        json={"name": "Temporary Project"},
        headers=user1_headers
    ).json()

    del_res = client.delete(f"/api/v1/projects/{project['id']}", headers=user1_headers)
    assert del_res.status_code == 204

    # Verify project is gone
    check_res = client.get(f"/api/v1/projects/{project['id']}", headers=user1_headers)
    assert check_res.status_code == 404


def test_delete_project_with_tasks_returns_409_conflict(
    client: TestClient,
    user1_headers: dict
):
    """
    Critical Business Rule:
    Ichida vazifasi bor loyihani o'chirish 409 bilan rad etilsin.
    """
    # 1. Create a project
    project = client.post(
        "/api/v1/projects",
        json={"name": "Important Project with Tasks"},
        headers=user1_headers
    ).json()

    # 2. Add a task to this project
    task_res = client.post(
        "/api/v1/tasks",
        json={
            "title": "Database Schema Design",
            "priority": "high",
            "project_id": project["id"]
        },
        headers=user1_headers
    )
    assert task_res.status_code == 201

    # 3. Attempt to delete the project -> MUST FAIL WITH 409 CONFLICT
    del_res = client.delete(f"/api/v1/projects/{project['id']}", headers=user1_headers)
    assert del_res.status_code == 409
    assert "contains" in del_res.json()["detail"].lower()
