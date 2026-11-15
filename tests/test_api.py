from uuid import uuid4

import pytest


def student(client, name="Анна"):
    response = client.post("/api/students", json={"name": name, "grade": "8", "goals": "Алгебра"})
    assert response.status_code == 201
    return response.json()["id"]


def lesson(client, student_id, date="2026-11-14T12:00:00+03:00", **extra):
    response = client.post(f"/api/students/{student_id}/lessons", json={
        "scheduled_at": date, "topic": "Квадратные уравнения", **extra,
    })
    assert response.status_code == 201
    return response.json()


def test_journal_and_partial_update(client):
    sid = student(client)
    assert client.get(f"/api/students/{sid}").json()["name"] == "Анна"
    assert client.get("/api/students").json()[0]["id"] == sid
    assert client.get("/api/students?limit=1&offset=1").json() == []
    updated = client.patch(f"/api/students/{sid}", json={"grade": None}).json()
    assert updated["grade"] is None and updated["goals"] == "Алгебра"
    entry = lesson(client, sid, notes="Ошибки со знаками", homework="Пять примеров")
    updated = client.patch(f"/api/lessons/{entry['id']}", json={"notes": "Стало лучше", "homework": None})
    assert updated.status_code == 200
    assert updated.json()["homework"] is None
    saved = client.get(f"/api/lessons/{entry['id']}").json()
    assert saved["notes"] == "Стало лучше" and saved["topic"] == entry["topic"]
    assert client.delete(f"/api/lessons/{entry['id']}").status_code == 204
    assert client.get(f"/api/lessons/{entry['id']}").status_code == 404
    assert client.get(f"/api/students/{sid}/lessons").json() == []


def test_history_order_dates_and_student_scope(client):
    sid, other = student(client), student(client, "Борис")
    first = lesson(client, sid, "2026-11-01T12:00:00Z")
    second = lesson(client, sid, "2026-11-08T12:00:00Z")
    lesson(client, other, "2026-11-09T12:00:00Z")
    path = f"/api/students/{sid}/lessons"
    assert [x["id"] for x in client.get(path).json()] == [second["id"], first["id"]]
    assert client.get(path, params={"limit": 1, "offset": 1}).json()[0]["id"] == first["id"]
    assert client.get(path, params={"date_from": second["scheduled_at"], "date_to": second["scheduled_at"]}).json() == [second]
    assert client.get(path, params={"date_to": "2026-10-01T00:00:00Z"}).json() == []
    assert client.get(path, params={"date_from": "2026-12-01T00:00:00Z", "date_to": "2026-10-01T00:00:00Z"}).status_code == 422
    assert client.get(path, params={"date_from": "2026-11-01T00:00:00"}).status_code == 422


def test_contacts_separate_and_cascade(client):
    sid, other = student(client), student(client, "Борис")
    entry = lesson(client, sid)
    response = client.post(f"/api/students/{sid}/contacts", json={
        "name": "Родитель", "phone": "+12025550101", "relationship": "мама",
    })
    assert response.status_code == 201
    cid = response.json()["id"]
    assert client.get(f"/api/students/{other}/contacts").json() == []
    assert len(client.get(f"/api/students/{sid}/contacts").json()) == 1
    assert "phone" not in str(client.get(f"/api/students/{sid}").json())
    assert "phone" not in str(client.get(f"/api/students/{sid}/lessons").json())
    assert client.patch(f"/api/contacts/{cid}", json={"phone": "+12025550102"}).status_code == 200
    assert client.get(f"/api/contacts/{cid}").json()["phone"] == "+12025550102"
    assert client.delete(f"/api/students/{sid}").status_code == 204
    assert client.get(f"/api/students/{sid}").status_code == 404
    assert client.get(f"/api/contacts/{cid}").status_code == 404
    assert client.get(f"/api/lessons/{entry['id']}").status_code == 404
    assert client.get(f"/api/students/{other}").status_code == 200


def test_delete_contact_keeps_student(client):
    sid = student(client)
    cid = client.post(f"/api/students/{sid}/contacts", json={"name": "Родитель", "phone": "+12025550101"}).json()["id"]
    assert client.delete(f"/api/contacts/{cid}").status_code == 204
    assert client.get(f"/api/students/{sid}/contacts").json() == []
    assert client.get(f"/api/students/{sid}").status_code == 200


@pytest.mark.parametrize("resource", ["students", "contacts", "lessons"])
def test_missing_records(client, resource):
    path = f"/api/{resource}/{uuid4()}"
    assert client.get(path).status_code == 404
    assert client.patch(path, json={}).status_code == 404
    assert client.delete(path).status_code == 404


def test_unknown_parent_and_invalid_inputs(client):
    missing = str(uuid4())
    assert client.get(f"/api/students/{missing}/lessons").status_code == 404
    assert client.get(f"/api/students/{missing}/contacts").status_code == 404
    assert client.post(f"/api/students/{missing}/lessons", json={"topic": "Тема", "scheduled_at": "2026-11-14T12:00:00Z"}).status_code == 404
    assert client.post(f"/api/students/{missing}/contacts", json={"name": "Родитель", "phone": "+12025550101"}).status_code == 404
    assert client.get("/api/students/not-a-uuid").status_code == 422
    for payload in ({"name": " "}, {"name": "А", "unknown": True}):
        assert client.post("/api/students", json=payload).status_code == 422
    sid = student(client)
    assert client.patch(f"/api/students/{sid}", json={"name": None}).status_code == 422
    assert client.post(f"/api/students/{sid}/contacts", json={"name": "Мама", "phone": "123"}).status_code == 422
    for date in ("2026-11-14T12:00:00", "bad"):
        assert client.post(f"/api/students/{sid}/lessons", json={"topic": "Тема", "scheduled_at": date}).status_code == 422
    entry = lesson(client, sid)
    assert client.patch(f"/api/lessons/{entry['id']}", json={"topic": None}).status_code == 422
    assert client.get("/api/students?limit=101").status_code == 422


def test_health_and_openapi(client):
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}
    assert client.get("/docs").status_code == 200
    assert "/api/students/{student_id}/lessons" in client.get("/openapi.json").json()["paths"]
