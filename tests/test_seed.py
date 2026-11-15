import asyncio
from pathlib import Path

from app.seed import import_seed


def test_seed_repeat_does_not_overwrite(client, database_url):
    path = Path("data/seed.json")
    assert asyncio.run(import_seed(path, database_url)) == {"students": 2, "contacts": 2, "lessons": 6}
    sid = client.get("/api/students").json()[0]["id"]
    client.patch(f"/api/students/{sid}", json={"name": "Изменено"})
    assert asyncio.run(import_seed(path, database_url)) == {"students": 0, "contacts": 0, "lessons": 0}
    assert client.get(f"/api/students/{sid}").json()["name"] == "Изменено"


def test_seed_conflict_rolls_back_all_new_records(client, database_url, tmp_path):
    import json
    from uuid import uuid4

    import pytest

    sid = client.post('/api/students', json={'name': 'Исходный'}).json()['id']
    contact = client.post(f'/api/students/{sid}/contacts', json={
        'name': 'Родитель', 'phone': '+12025550101',
    }).json()
    new_id = str(uuid4())
    path = tmp_path / 'conflict.json'
    path.write_text(json.dumps({'students': [{
        'id': new_id, 'name': 'Не должен сохраниться',
        'contacts': [{'id': contact['id'], 'name': 'Чужой', 'phone': '+12025550102'}],
    }]}))
    with pytest.raises(ValueError, match='belongs to another student'):
        asyncio.run(import_seed(path, database_url))
    assert client.get(f'/api/students/{new_id}').status_code == 404
    assert client.get(f"/api/contacts/{contact['id']}").json()['student_id'] == sid
