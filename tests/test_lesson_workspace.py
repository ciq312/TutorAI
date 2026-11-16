"""Persist the teacher's actual workflow, without invoking cloud models."""
import pytest


def records(client):
    student = client.post('/api/students', json={'name': 'Тестовый ученик'}).json()
    lesson = client.post(f"/api/students/{student['id']}/lessons", json={
        'topic': 'Квадратные уравнения', 'scheduled_at': '2026-11-14T10:00:00Z',
        'duration_minutes': 45, 'preparation_minutes': 20,
    }).json()
    return student, lesson


def test_materials_persist_and_homework_is_only_assigned_after_acceptance(client):
    _, lesson = records(client)
    url = f"/api/lessons/{lesson['id']}"
    draft = {'text': 'Решить x² − 3x − 4 = 0', 'answers': 'Корни: 4 и −1', 'sources': []}
    materials = {'plan': {'text': 'Повторение и практика', 'brief': 'Повторить знаки'},
                 'homework': draft, 'next_plan': {'text': 'Перейти к теореме Виета'},
                 'next_topic': 'Теорема Виета'}
    response = client.patch(url, json={'materials': materials})
    assert response.status_code == 200, response.text
    # Editing drafts alone must not change lesson indexing or assign homework.
    assert response.json()['indexing_status'] == lesson['indexing_status']
    read = client.get(url).json()
    assert read['materials']['homework']['answers'] == draft['answers']
    assert read['homework'] is None
    assert read['duration_minutes'] == 45
    accepted = client.put(url + '/homework', json={'homework': draft['text']})
    assert accepted.status_code == 200
    assert client.get(url).json()['homework'] == draft['text']
    assert client.get(url).json()['materials']['homework']['answers'] == draft['answers']


def test_completion_reschedule_and_cancellation_are_explicit(client):
    student, lesson = records(client)
    url = f"/api/lessons/{lesson['id']}"
    assert lesson['status'] == 'scheduled'
    completed = client.patch(url, json={'notes': 'Решили три примера', 'status': 'completed'})
    assert completed.status_code == 200
    assert completed.json()['status'] == 'completed'
    moved = client.patch(url, json={'scheduled_at': '2026-11-16T10:00:00Z'})
    assert moved.status_code == 200
    assert moved.json()['notes'] == 'Решили три примера'
    assert client.patch(url, json={'status': 'cancelled'}).status_code == 200
    context = client.post(f"/api/students/{student['id']}/context/search", json={
        'query': 'уравнения', 'semantic_limit': 0})
    assert context.status_code == 200
    assert context.json()['sources'] == []
    assert client.patch(url, json={'status': 'scheduled'}).status_code == 200
    assert client.get(url).json()['notes'] == 'Решили три примера'


@pytest.mark.parametrize('patch', [
    {'status': None}, {'status': 'unknown'}, {'materials': None},
    {'duration_minutes': 0}, {'preparation_minutes': -1},
    {'materials': {'homework': {'text': 'a' * 20001}}},
])
def test_workspace_validation(client, patch):
    _, lesson = records(client)
    assert client.patch(f"/api/lessons/{lesson['id']}", json=patch).status_code == 422
