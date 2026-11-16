"""Exercise integration boundaries with real PostgreSQL and fake external HTTP, never live accounts."""
import json
from datetime import timedelta
from uuid import UUID
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.db.models import CalendarEvent, CalendarSeries, Lesson, Student, NotificationDelivery
from app.services import integrations as svc
from app.worker import notification_tick


def db(client, action):
    async def run():
        async with client.app.state.session_factory() as session, session.begin():
            return await action(session)
    return client.portal.call(run)


def configure(client, handler):
    settings = client.app.state.settings
    settings.google_client_id = 'client-id'
    from pydantic import SecretStr
    settings.google_client_secret = SecretStr('client-secret')
    settings.integration_encryption_key = SecretStr(Fernet.generate_key().decode())
    settings.telegram_bot_token = SecretStr('test-bot-token')
    client.app.state.integration_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async def prepare(session):
        row = await svc.state(session)
        svc.save_state(row, {'google_access': svc.encrypt(settings, 'access-secret'),
            'google_refresh': svc.encrypt(settings, 'refresh-secret'),
            'google_expires': (svc.now()+timedelta(hours=1)).isoformat(),
            'calendars': [{'calendar_id': 'mixed@example.test', 'mode': 'mixed'}]})
    db(client, prepare)


def event_item(id='event-one', **patch):
    start = svc.now()+timedelta(hours=1)
    return {'id': id, 'etag': 'v1', 'summary': 'Математика — Саша',
            'start': {'dateTime': start.isoformat()},
            'end': {'dateTime': (start+timedelta(hours=1)).isoformat()},
            'description': 'Ссылка на встречу', **patch}


def test_calendar_import_is_not_a_lesson_until_linked_and_series_is_idempotent(client):
    items = [event_item('one', recurringEventId='series'), event_item('two', recurringEventId='series'),
             event_item('personal', summary='Мой курс')]
    configure(client, lambda r: httpx.Response(200, json={'items': items}))
    assert client.post('/api/integrations/google/sync').status_code == 200
    assert client.get('/api/students').json() == []
    events = client.get('/api/integrations/google/events').json()
    first = next(e for e in events if e['external_id'] == 'one')
    linked = client.post(f"/api/integrations/google/events/{first['id']}/decision", json={
        'action':'link','new_student':{'name':'Саша'},'whole_series':True})
    assert linked.status_code == 200, linked.text
    student_id = linked.json()['student']['id']
    assert len(client.get(f'/api/students/{student_id}/lessons').json()) == 2
    assert client.post('/api/integrations/google/sync').status_code == 200
    assert len(client.get(f'/api/students/{student_id}/lessons').json()) == 2
    # Future series instances attach automatically only after the tutor's series decision.
    items.append(event_item('three', recurringEventId='series'))
    client.post('/api/integrations/google/sync')
    assert len(client.get(f'/api/students/{student_id}/lessons').json()) == 3
    assert len(client.get('/api/students').json()) == 1
    personal = next(e for e in events if e['external_id']=='personal')
    assert client.post(f"/api/integrations/google/events/{personal['id']}/decision", json={'action':'ignore'}).status_code == 200
    assert client.get('/api/integrations/google/events?decision=ignored').json()[0]['id'] == personal['id']


def test_google_pagination_reschedule_cancel_and_reinstate(client):
    first = event_item('one')
    second = event_item('two')
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(200,json={'items':[second]} if request.url.params.get('pageToken') else {'items':[first],'nextPageToken':'page2'})
    configure(client, handler)
    client.post('/api/integrations/google/sync')
    assert len(requests)==2
    event = next(e for e in client.get('/api/integrations/google/events').json() if e['external_id']=='one')
    linked=client.post(f"/api/integrations/google/events/{event['id']}/decision",json={'action':'link','new_student':{'name':'Саша'}}).json()
    lesson_id=linked['lesson']['id']
    moved=svc.now()+timedelta(days=2)
    first.update(start={'dateTime':moved.isoformat()},end={'dateTime':(moved+timedelta(hours=1)).isoformat()})
    client.post('/api/integrations/google/sync')
    assert client.get(f'/api/lessons/{lesson_id}').json()['scheduled_at'].startswith(moved.isoformat()[:19])
    first['status']='cancelled'
    client.post('/api/integrations/google/sync')
    assert client.get(f'/api/lessons/{lesson_id}').json()['status']=='cancelled'
    first['status']='confirmed'
    client.post('/api/integrations/google/sync')
    assert client.get(f'/api/lessons/{lesson_id}').json()['status']=='scheduled'
    first.update(start={'date':'2026-11-20'},end={'date':'2026-11-21'})
    client.post('/api/integrations/google/sync')
    assert client.get(f'/api/lessons/{lesson_id}').json()['status']=='cancelled'


def prepare_linked(client, handler):
    configure(client, handler)
    async def seed(session):
        event=await svc.upsert_event(session,'mixed@example.test',event_item())
        student=Student(name='Саша');session.add(student);await session.flush()
        lesson=await svc.attach(session,event,student.id)
        lesson.homework='Решить № 5'
        return str(lesson.id)
    return db(client,seed)


def test_calendar_homework_requires_explicit_approval_preserves_description_and_is_idempotent(client):
    item=event_item()
    patches=[]
    def handler(request):
        if request.method=='PATCH':
            assert request.headers['if-match']=='v1'
            patches.append(json.loads(request.content))
            item.update(patches[-1]);item['etag']='v2'
        return httpx.Response(200,json=item)
    lesson_id=prepare_linked(client,handler)
    preview=client.post(f'/api/integrations/lessons/{lesson_id}/calendar-homework/preview')
    assert preview.status_code==200,preview.text
    assert not patches
    approval=preview.json()
    assert 'Ссылка на встречу' in approval['description'] and 'Решить № 5' in approval['description']
    for _ in range(2):
        assert client.post(f"/api/integrations/calendar-approvals/{approval['id']}/confirm").status_code==200
    assert len(patches)==1 and set(patches[0])=={'description'}
    assert svc.homework_description(item['description'],'Новое ДЗ').count(svc.BLOCK_START)==1


def test_changed_homework_or_external_event_blocks_stale_approval(client):
    item=event_item()
    patches=[]
    def handler(request):
        if request.method=='PATCH':patches.append(request)
        return httpx.Response(200,json=item)
    lesson=prepare_linked(client,handler)
    preview=lambda:client.post(f'/api/integrations/lessons/{lesson}/calendar-homework/preview').json()
    approval=preview()
    client.put(f'/api/lessons/{lesson}/homework',json={'homework':'Изменённое ДЗ'})
    assert client.post(f"/api/integrations/calendar-approvals/{approval['id']}/confirm").status_code==409
    approval=preview();item['etag']='changed-in-google'
    assert client.post(f"/api/integrations/calendar-approvals/{approval['id']}/confirm").status_code==409
    assert patches==[]


def test_oauth_cookie_state_single_use_and_credentials_never_returned(client):
    configure(client,lambda request:httpx.Response(200,json={'access_token':'new-secret','refresh_token':'new-refresh','expires_in':3600,'scope':svc.SCOPES}))
    url=client.post('/api/integrations/google/connect').json()['url']
    state=parse_qs(urlparse(url).query)['state'][0]
    assert client.get('/api/integrations/google/callback',params={'state':'bad','code':'x'}).status_code==400
    callback=client.get('/api/integrations/google/callback',params={'state':state,'code':'x'},follow_redirects=False)
    assert callback.status_code==303,callback.text
    assert client.get('/api/integrations/google/callback',params={'state':state,'code':'x'}).status_code==400
    status=client.get('/api/integrations/status')
    assert status.json()['google_connected']
    assert all(secret not in status.text for secret in ['new-secret','new-refresh','client-secret'])
    assert client.delete('/api/integrations/google').status_code==204
    assert not client.get('/api/integrations/status').json()['google_connected']


def test_telegram_link_only_private_chat_with_unexpired_one_time_code(client):
    updates=[]
    def handler(request):
        return httpx.Response(200,json={'ok':True,'result':{'username':'tutor_test_bot'} if request.url.path.endswith('getMe') else updates})
    configure(client,handler)
    url=client.post('/api/integrations/telegram/connect').json()['url']
    code=parse_qs(urlparse(url).query)['start'][0]
    updates.append({'update_id':1,'message':{'text':'/start '+code,'chat':{'id':1,'type':'group'}}})
    assert client.post('/api/integrations/telegram/check').json()['connected'] is False
    updates.append({'update_id':2,'message':{'text':'/start '+code,'chat':{'id':2,'type':'private'}}})
    assert client.post('/api/integrations/telegram/check').json()['connected'] is True
    async def inspect(session):return (await svc.state(session)).data
    data=db(client,inspect)
    assert data['telegram_chat']=='2' and 'telegram_link' not in data and data['telegram_offset']==3
    assert client.delete('/api/integrations/telegram').status_code==204
    # A consumed old code cannot reconnect after disconnection.
    assert client.post('/api/integrations/telegram/check').json()['connected'] is False


def test_notification_outbox_no_duplicates_cancelled_lessons_and_unknown_send(client):
    sends=[]
    def handler(request):
        sends.append(json.loads(request.content))
        return httpx.Response(200,json={'ok':True,'result':{'message_id':1}})
    lesson_id=prepare_linked(client,handler)
    async def seed(session):
        row=await svc.state(session);svc.save_state(row,{**row.data,'telegram_chat':'123'})
        lesson=await session.get(Lesson,UUID(lesson_id));lesson.scheduled_at=svc.now()+timedelta(minutes=10)
    db(client,seed)
    async def tick():await notification_tick(client.app.state.session_factory,client.app.state.settings,client.app.state.integration_client)
    client.portal.call(tick);client.portal.call(tick)
    assert len(sends)==1 and 'Решения' not in sends[0]['text']
    assert client.get('/api/integrations/notifications/deliveries').json()[0]['status']=='sent'
    # Moving a lesson changes the reminder key; ambiguous sends never auto-repeat.
    client.patch(f'/api/lessons/{lesson_id}',json={'scheduled_at':(svc.now()+timedelta(minutes=11)).isoformat()})
    async def fail(request):raise httpx.ReadTimeout('private credential url',request=request)
    client.app.state.integration_client=httpx.AsyncClient(transport=httpx.MockTransport(fail))
    client.portal.call(tick);client.portal.call(tick)
    statuses=[d['status'] for d in client.get('/api/integrations/notifications/deliveries').json()]
    assert statuses.count('uncertain')==1
    client.patch(f'/api/lessons/{lesson_id}',json={'status':'cancelled'})
    client.portal.call(tick)
    assert len(client.get('/api/integrations/notifications/deliveries').json())==2


@pytest.mark.parametrize('body',[{'before_minutes':-1},{'timezone':'Not/A/Zone'},{'before_minutes':None}])
def test_notification_settings_validation(client,body):
    assert client.put('/api/integrations/notifications',json=body).status_code==422


def test_worker_google_sync_continues_when_telegram_poll_fails(client):
    from app.worker import integration_tick
    def handler(request):
        if request.url.path.endswith('/getUpdates'):
            return httpx.Response(500,json={'ok':False})
        return httpx.Response(200,json={'items':[event_item()]})
    configure(client,handler)
    async def tick():
        await integration_tick(client.app.state.session_factory,client.app.state.settings,client.app.state.integration_client)
    client.portal.call(tick)
    status=client.get('/api/integrations/status').json()
    assert status['last_sync'] and status['worker_heartbeat']
    assert status['worker_error']=='telegram_poll_failed'
    assert len(client.get('/api/integrations/google/events').json())==1


def test_expired_google_access_token_is_refreshed_and_stored_encrypted(client):
    calls=[]
    def handler(request):
        calls.append(request)
        if request.url.host=='oauth2.googleapis.com':
            assert parse_qs(request.content.decode())['refresh_token']==['refresh-secret']
            return httpx.Response(200,json={'access_token':'renewed-access','expires_in':3600})
        assert request.headers['authorization']=='Bearer renewed-access'
        return httpx.Response(200,json={'items':[]})
    configure(client,handler)
    async def expire(session):
        row=await svc.state(session)
        svc.save_state(row,{**row.data,'google_expires':(svc.now()-timedelta(minutes=1)).isoformat()})
    db(client,expire)
    assert client.post('/api/integrations/google/sync').status_code==200
    assert len(calls)==2
    async def stored(session):return (await svc.state(session)).data['google_access']
    encrypted=db(client,stored)
    assert encrypted!='renewed-access'
    assert svc.decrypt(client.app.state.settings,encrypted)=='renewed-access'
