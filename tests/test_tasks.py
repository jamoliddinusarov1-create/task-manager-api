from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def test_create_task_and_details(client: TestClient, user1_headers: dict):
    """Test creating a task within user's project and retrieving details."""
    p = client.post("/api/v1/projects", json={"name": "P1"}, headers=user1_headers).json()

    task_payload = {
        "title": "Write API documentation",
        "description": "Document all routes in Swagger",
        "priority": "high",
        "project_id": p["id"],
        "deadline": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    }
    res = client.post("/api/v1/tasks", json=task_payload, headers=user1_headers)
    assert res.status_code == 201
    task_data = res.json()
    assert task_data["title"] == "Write API documentation"
    assert task_data["priority"] == "high"
    assert task_data["completed_at"] is None

    # Get details
    get_res = client.get(f"/api/v1/tasks/{task_data['id']}", headers=user1_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_data["id"]


def test_cannot_attach_task_to_other_users_project(
    client: TestClient,
    user1_headers: dict,
    user2_headers: dict
):
    """
    Business Rule:
    Vazifa faqat egasining loyihasiga bog'lansin.
    User 2 cannot attach a task to User 1's project -> returns 404.
    """
    u1_project = client.post(
        "/api/v1/projects",
        json={"name": "User 1 Project"},
        headers=user1_headers
    ).json()

    # User 2 tries to create task using User 1's project_id
    u2_task_res = client.post(
        "/api/v1/tasks",
        json={
            "title": "Malicious Task",
            "priority": "low",
            "project_id": u1_project["id"]
        },
        headers=user2_headers
    )
    assert u2_task_res.status_code == 404


def test_tasks_isolation_between_two_users(
    client: TestClient,
    user1_headers: dict,
    user2_headers: dict
):
    """
    Exam Defense Demonstration:
    Ikki foydalanuvchi yarating. Ikkinchisi birinchining vazifasini
    ko'ra yoki tahrirlay olmasin.
    """
    p1 = client.post("/api/v1/projects", json={"name": "U1 Proj"}, headers=user1_headers).json()
    t1 = client.post(
        "/api/v1/tasks",
        json={"title": "U1 Secret Task", "project_id": p1["id"]},
        headers=user1_headers
    ).json()

    # User 2 cannot see t1 in tasks list
    u2_list = client.get("/api/v1/tasks", headers=user2_headers).json()
    assert len(u2_list) == 0

    # User 2 cannot GET t1 detail -> returns 404
    u2_get = client.get(f"/api/v1/tasks/{t1['id']}", headers=user2_headers)
    assert u2_get.status_code == 404

    # User 2 cannot update t1 -> returns 404
    u2_put = client.put(
        f"/api/v1/tasks/{t1['id']}",
        json={"title": "Hacked"},
        headers=user2_headers
    )
    assert u2_put.status_code == 404

    # User 2 cannot mark t1 completed -> returns 404
    u2_patch = client.patch(
        f"/api/v1/tasks/{t1['id']}/status",
        json={"completed": True},
        headers=user2_headers
    )
    assert u2_patch.status_code == 404

    # User 2 cannot delete t1 -> returns 404
    u2_del = client.delete(f"/api/v1/tasks/{t1['id']}", headers=user2_headers)
    assert u2_del.status_code == 404


def test_priority_custom_sorting(client: TestClient, user1_headers: dict):
    """
    Business Rule:
    Saralash alifbo tartibida emas, high -> medium -> low tartibida bo'lsin.
    (Alphabetical would be: high, low, medium - which is incorrect).
    """
    p = client.post("/api/v1/projects", json={"name": "Sort Proj"}, headers=user1_headers).json()

    # Create in random order: Low, High, Medium
    client.post(
        "/api/v1/tasks",
        json={"title": "Low Task", "priority": "low", "project_id": p["id"]},
        headers=user1_headers
    )
    client.post(
        "/api/v1/tasks",
        json={"title": "High Task", "priority": "high", "project_id": p["id"]},
        headers=user1_headers
    )
    client.post(
        "/api/v1/tasks",
        json={"title": "Medium Task", "priority": "medium", "project_id": p["id"]},
        headers=user1_headers
    )

    # Fetch sorted by priority
    res = client.get("/api/v1/tasks?sort_by=priority", headers=user1_headers)
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 3
    assert tasks[0]["priority"] == "high"
    assert tasks[1]["priority"] == "medium"
    assert tasks[2]["priority"] == "low"


def test_task_status_toggle_and_completed_at(client: TestClient, user1_headers: dict):
    """
    Business Rule:
    Bajarilganda completed_at o'rnatilsin; qayta ochilganda tozalansin (None).
    """
    p = client.post("/api/v1/projects", json={"name": "Status Proj"}, headers=user1_headers).json()
    t = client.post("/api/v1/tasks", json={"title": "Status Task", "project_id": p["id"]}, headers=user1_headers).json()
    task_id = t["id"]
    assert t["completed_at"] is None

    # Mark completed
    complete_res = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"completed": True},
        headers=user1_headers
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["completed_at"] is not None

    # Reopen
    reopen_res = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"completed": False},
        headers=user1_headers
    )
    assert reopen_res.status_code == 200
    assert reopen_res.json()["completed_at"] is None


def test_overdue_tasks_logic(client: TestClient, user1_headers: dict):
    """
    Business Rule & Exam Defense:
    Overdue: deadline < hozir va vazifa bajarilmagan.
    Bajarilgan eski vazifa overdue ro'yxatiga kirmasin!
    """
    p = client.post("/api/v1/projects", json={"name": "Overdue Proj"}, headers=user1_headers).json()
    past_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()

    # 1. Past deadline, uncompleted -> MUST BE OVERDUE
    t1 = client.post(
        "/api/v1/tasks",
        json={"title": "Past Uncompleted", "project_id": p["id"], "deadline": past_date},
        headers=user1_headers
    ).json()

    # 2. Future deadline, uncompleted -> NOT overdue
    client.post(
        "/api/v1/tasks",
        json={"title": "Future Task", "project_id": p["id"], "deadline": future_date},
        headers=user1_headers
    )

    # 3. Past deadline, but COMPLETED -> MUST NOT BE IN OVERDUE!
    t3 = client.post(
        "/api/v1/tasks",
        json={"title": "Past but Completed", "project_id": p["id"], "deadline": past_date},
        headers=user1_headers
    ).json()
    client.patch(
        f"/api/v1/tasks/{t3['id']}/status",
        json={"completed": True},
        headers=user1_headers
    )

    # Fetch overdue list
    overdue_res = client.get("/api/v1/tasks/overdue", headers=user1_headers)
    assert overdue_res.status_code == 200
    overdue_tasks = overdue_res.json()
    overdue_ids = [t["id"] for t in overdue_tasks]

    assert t1["id"] in overdue_ids
    assert t3["id"] not in overdue_ids  # Completed old task is NEVER overdue!


def test_task_statistics(client: TestClient, user1_headers: dict, user2_headers: dict):
    """
    Business Rule:
    O'z vazifalari bo'yicha jami, bajarilgan va bajarilmagan sonlarni olish.
    Boshqa foydalanuvchi ma'lumotlarini hisoblamaslik.
    """
    p1 = client.post("/api/v1/projects", json={"name": "Stats P1"}, headers=user1_headers).json()
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    # User 1 creates 3 tasks: 1 completed, 2 uncompleted (1 overdue)
    t1 = client.post("/api/v1/tasks", json={"title": "T1", "project_id": p1["id"]}, headers=user1_headers).json()
    client.patch(f"/api/v1/tasks/{t1['id']}/status", json={"completed": True}, headers=user1_headers)

    client.post(
        "/api/v1/tasks",
        json={"title": "T2", "project_id": p1["id"], "deadline": past_date},
        headers=user1_headers
    )
    client.post("/api/v1/tasks", json={"title": "T3", "project_id": p1["id"]}, headers=user1_headers)

    # User 2 creates 1 task (should not affect User 1's stats)
    p2 = client.post("/api/v1/projects", json={"name": "Stats P2"}, headers=user2_headers).json()
    client.post("/api/v1/tasks", json={"title": "U2 Task", "project_id": p2["id"]}, headers=user2_headers)

    # Check stats for User 1
    stats_res = client.get("/api/v1/tasks/stats", headers=user1_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total"] == 3
    assert stats["completed"] == 1
    assert stats["uncompleted"] == 2
    assert stats["overdue"] == 1
