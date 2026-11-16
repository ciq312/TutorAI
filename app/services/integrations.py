"""Single-tutor integrations. Credentials never leave the server."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, quote
from uuid import UUID

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import IntegrationState, CalendarEvent, CalendarSeries, CalendarApproval, Lesson, Student
from app.schemas.integrations import NotificationSettings
from app.services.records import require_record

GOOGLE_API = 'https://www.googleapis.com/calendar/v3'
SCOPES = 'https://www.googleapis.com/auth/calendar.calendarlist.readonly https://www.googleapis.com/auth/calendar.events'


def now():
    return datetime.now(timezone.utc)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


async def state(session, lock=True):
    query = select(IntegrationState).where(IntegrationState.id == 1)
    row = await session.scalar(query.with_for_update() if lock else query)
    if row is None:
        await session.execute(insert(IntegrationState).values(id=1, data={}).on_conflict_do_nothing())
        row = await session.scalar(query.with_for_update() if lock else query)
    return row


def save_state(row, data):
    row.data = dict(data)


def cipher(settings):
    try:
        return Fernet(settings.integration_encryption_key.get_secret_value().encode())
    except (ValueError, TypeError):
        raise HTTPException(503, detail={'code': 'integration_key_missing'}) from None


def encrypt(settings, value):
    return cipher(settings).encrypt(value.encode()).decode()


def decrypt(settings, value):
    try:
        return cipher(settings).decrypt(value.encode()).decode()
    except InvalidToken:
        raise HTTPException(503, detail={'code': 'integration_key_invalid'}) from None


async def external(client, method, url, **kwargs):
    try:
        response = await client.request(method, url, **kwargs)
    except httpx.RequestError:
        raise HTTPException(503, detail={'code': 'integration_unavailable'}) from None
    if response.status_code in (409, 412):
        raise HTTPException(409, detail={'code': 'calendar_changed'})
    if not response.is_success:
        code = 'integration_reconnect_required' if response.status_code in (400, 401, 403) else 'integration_unavailable'
        raise HTTPException(503, detail={'code': code})
    try:
        return response.json()
    except ValueError:
        raise HTTPException(502, detail={'code': 'integration_invalid_response'}) from None


async def begin_oauth(session, settings):
    if not settings.google_client_id or not settings.google_client_secret.get_secret_value():
        raise HTTPException(503, detail={'code': 'google_not_configured'})
    cipher(settings)
    row = await state(session)
    value = secrets.token_urlsafe(32)
    data = {**row.data, 'oauth_state': digest(value), 'oauth_expires': (now() + timedelta(minutes=10)).isoformat()}
    save_state(row, data)
    return value, 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
        'client_id': settings.google_client_id, 'redirect_uri': settings.google_redirect_uri,
        'response_type': 'code', 'scope': SCOPES, 'access_type': 'offline', 'prompt': 'consent', 'state': value,
    })


async def complete_oauth(session, settings, client, value, code):
    row = await state(session)
    data = dict(row.data)
    if (not value or not secrets.compare_digest(data.get('oauth_state', ''), digest(value))
            or datetime.fromisoformat(data.get('oauth_expires', '2000-01-01T00:00:00+00:00')) < now()):
        raise HTTPException(400, detail={'code': 'oauth_state_invalid'})
    token = await external(client, 'POST', 'https://oauth2.googleapis.com/token', data={
        'client_id': settings.google_client_id, 'client_secret': settings.google_client_secret.get_secret_value(),
        'code': code, 'grant_type': 'authorization_code', 'redirect_uri': settings.google_redirect_uri,
    })
    if not token.get('refresh_token') or not token.get('access_token'):
        raise HTTPException(502, detail={'code': 'google_refresh_token_missing'})
    if not set(SCOPES.split()).issubset(set(token.get('scope', '').split())):
        raise HTTPException(400, detail={'code': 'google_scopes_missing'})
    data.pop('oauth_state', None)
    data.pop('oauth_expires', None)
    data.update(google_access=encrypt(settings, token['access_token']),
                google_refresh=encrypt(settings, token['refresh_token']),
                google_expires=(now() + timedelta(seconds=token.get('expires_in', 3600))).isoformat(),
                calendars=[], last_sync=None, sync_error=None)
    save_state(row, data)


async def google_headers(row, settings, client):
    data = dict(row.data)
    if not data.get('google_refresh'):
        raise HTTPException(409, detail={'code': 'google_not_connected'})
    if datetime.fromisoformat(data['google_expires']) <= now() + timedelta(seconds=60):
        token = await external(client, 'POST', 'https://oauth2.googleapis.com/token', data={
            'client_id': settings.google_client_id, 'client_secret': settings.google_client_secret.get_secret_value(),
            'refresh_token': decrypt(settings, data['google_refresh']), 'grant_type': 'refresh_token',
        })
        if not token.get('access_token'):
            raise HTTPException(502, detail={'code': 'integration_invalid_response'})
        data.update(google_access=encrypt(settings, token['access_token']),
                    google_expires=(now() + timedelta(seconds=token.get('expires_in', 3600))).isoformat())
        save_state(row, data)
    return {'Authorization': 'Bearer ' + decrypt(settings, data['google_access'])}


async def calendar_list(row, settings, client):
    headers = await google_headers(row, settings, client)
    result, page = [], None
    while True:
        payload = await external(client, 'GET', GOOGLE_API + '/users/me/calendarList',
                                 headers=headers, params={'maxResults': 250, **({'pageToken': page} if page else {})})
        result.extend({'id': c['id'], 'summary': c.get('summary', c['id']),
                       'access_role': c.get('accessRole', 'reader')} for c in payload.get('items', []))
        page = payload.get('nextPageToken')
        if not page:
            return result


def event_url(event):
    return GOOGLE_API + '/calendars/' + quote(event.calendar_id, safe='') + '/events/' + quote(event.external_id, safe='')


def parse_date(value):
    if not value or not value.get('dateTime'):
        return None  # All-day events remain visible but cannot become timed lessons.
    result = datetime.fromisoformat(value['dateTime'].replace('Z', '+00:00'))
    if result.tzinfo is None:
        from zoneinfo import ZoneInfo
        result = result.replace(tzinfo=ZoneInfo(value.get('timeZone', 'UTC')))
    return result


async def attach(session, event, student_id):
    if event.status == 'cancelled' or not event.starts_at or not event.ends_at:
        raise HTTPException(409, detail={'code': 'event_not_teachable'})
    duration = round((event.ends_at - event.starts_at).total_seconds() / 60)
    if not 10 <= duration <= 240:
        raise HTTPException(409, detail={'code': 'event_duration_invalid'})
    if event.lesson_id:
        lesson = await require_record(session, Lesson, event.lesson_id)
        if lesson.student_id != student_id:
            raise HTTPException(409, detail={'code': 'event_already_linked'})
        return lesson
    lesson = Lesson(student_id=student_id, scheduled_at=event.starts_at, duration_minutes=duration,
                    preparation_minutes=30, topic=event.title or 'Занятие', status='scheduled', materials={})
    session.add(lesson)
    await session.flush()
    event.lesson_id, event.decision = lesson.id, 'linked'
    return lesson


async def upsert_event(session, calendar_id, item):
    event = await session.scalar(select(CalendarEvent).where(
        CalendarEvent.calendar_id == calendar_id, CalendarEvent.external_id == item['id']))
    if event is None:
        event = CalendarEvent(calendar_id=calendar_id, external_id=item['id'], title='', decision='pending')
        session.add(event)
    if event.decision == 'linked' and event.lesson_id is None:
        event.decision = 'pending'
    old_status = event.status
    old_title = event.title
    old_timed = bool(event.starts_at and event.ends_at)
    event.status = item.get('status', 'confirmed')
    event.etag = item.get('etag', '')
    if item.get('summary') is not None:
        event.title = item['summary'][:500]
    event.series_id = item.get('recurringEventId', event.series_id)
    if 'start' in item:
        event.starts_at = parse_date(item['start'])
    if 'end' in item:
        event.ends_at = parse_date(item['end'])
    if 'description' in item:
        event.description = item['description']
    if event.lesson_id:
        lesson = await session.get(Lesson, event.lesson_id)
        timed = bool(event.starts_at and event.ends_at)
        duration = (event.ends_at-event.starts_at).total_seconds()/60 if timed else 0
        if lesson and (event.status == 'cancelled' or not 10 <= duration <= 240):
            lesson.status = 'cancelled'
        elif lesson and lesson.status != 'completed':
            if lesson.topic == old_title and event.title != old_title:
                lesson.topic = event.title or 'Занятие'
                lesson.indexing_status = 'pending'
            if event.starts_at:
                lesson.scheduled_at = event.starts_at
            if event.starts_at and event.ends_at:
                lesson.duration_minutes = max(10, min(240, round((event.ends_at - event.starts_at).total_seconds()/60)))
            if old_status == 'cancelled' or not old_timed:
                lesson.status = 'scheduled'
    elif event.decision == 'pending' and event.series_id and event.status != 'cancelled':
        series = await session.scalar(select(CalendarSeries).where(
            CalendarSeries.calendar_id == calendar_id, CalendarSeries.external_id == event.series_id))
        if series and event.starts_at and event.ends_at and 10 <= (event.ends_at-event.starts_at).total_seconds()/60 <= 240:
            await attach(session, event, series.student_id)
    return event


async def sync_calendars(session, row, settings, client):
    headers = await google_headers(row, settings, client)
    count = 0
    for chosen in row.data.get('calendars', []):
        calendar_id, page, seen = chosen['calendar_id'], None, set()
        # A rolling window deliberately uses full pagination instead of mixing timeMin with syncToken.
        while True:
            params = {'singleEvents': 'true', 'showDeleted': 'true', 'maxResults': 250,
                      'timeMin': (now()-timedelta(days=30)).isoformat(),
                      'timeMax': (now()+timedelta(days=180)).isoformat()}
            if page:
                params['pageToken'] = page
            payload = await external(client, 'GET', GOOGLE_API + '/calendars/' + quote(calendar_id, safe='') + '/events',
                                     headers=headers, params=params)
            for item in payload.get('items', []):
                seen.add(item['id'])
                await upsert_event(session, calendar_id, item)
                count += 1
            page = payload.get('nextPageToken')
            if not page:
                break
        # Resolve previously imported future events omitted from the new window (moved/deleted).
        missing = (await session.scalars(select(CalendarEvent).where(
            CalendarEvent.calendar_id == calendar_id, CalendarEvent.starts_at >= now()-timedelta(days=30),
            CalendarEvent.status != 'cancelled'))).all()
        for event in missing:
            if event.external_id in seen:
                continue
            try:
                response = await client.get(event_url(event), headers=headers)
            except httpx.RequestError:
                raise HTTPException(503, detail={'code': 'integration_unavailable'}) from None
            if response.status_code in (404, 410):
                await upsert_event(session, calendar_id, {'id': event.external_id, 'status': 'cancelled'})
            elif response.is_success:
                await upsert_event(session, calendar_id, response.json())
            else:
                raise HTTPException(503, detail={'code': 'integration_unavailable'})
    save_state(row, {**row.data, 'last_sync': now().isoformat(), 'sync_error': None})
    return count


BLOCK_START = '[My Tutor AI — ДЗ]'
BLOCK_END = '[/My Tutor AI — ДЗ]'


def homework_description(description, homework):
    start, end = description.find(BLOCK_START), description.find(BLOCK_END)
    if start >= 0 and end >= start:
        description = description[:start] + description[end+len(BLOCK_END):]
    return description.rstrip() + '\n\n' + BLOCK_START + '\n' + homework + '\n' + BLOCK_END


async def preview_homework(session, lesson_id, row, settings, client):
    lesson = await require_record(session, Lesson, lesson_id)
    event = await session.scalar(select(CalendarEvent).where(CalendarEvent.lesson_id == lesson_id))
    selected = {c['calendar_id'] for c in row.data.get('calendars', [])}
    if not event or event.calendar_id not in selected or event.status == 'cancelled' or not lesson.homework:
        raise HTTPException(409, detail={'code': 'calendar_homework_unavailable'})
    headers = await google_headers(row, settings, client)
    item = await external(client, 'GET', event_url(event), headers=headers)
    await upsert_event(session, event.calendar_id, item)
    if event.status == 'cancelled':
        raise HTTPException(409, detail={'code': 'event_cancelled'})
    approval = CalendarApproval(event_id=event.id, homework=lesson.homework,
                                description=homework_description(item.get('description', ''), lesson.homework),
                                etag=item['etag'], expires_at=now()+timedelta(minutes=15), status='pending')
    session.add(approval)
    await session.flush()
    return approval, event


async def confirm_homework(session, approval_id, row, settings, client):
    approval = await session.scalar(select(CalendarApproval).where(CalendarApproval.id == approval_id).with_for_update())
    if not approval:
        raise HTTPException(404)
    if approval.status == 'applied':
        return approval
    if approval.status != 'pending' or approval.expires_at < now():
        raise HTTPException(409, detail={'code': 'approval_expired'})
    event = await require_record(session, CalendarEvent, approval.event_id)
    lesson = await require_record(session, Lesson, event.lesson_id) if event.lesson_id else None
    if not lesson or lesson.homework != approval.homework or lesson.status == 'cancelled':
        raise HTTPException(409, detail={'code': 'approval_stale'})
    if event.calendar_id not in {c['calendar_id'] for c in row.data.get('calendars', [])}:
        raise HTTPException(409, detail={'code': 'google_not_connected'})
    headers = await google_headers(row, settings, client)
    current = await external(client, 'GET', event_url(event), headers=headers)
    # Recover safely if Google accepted a previous request but the local commit was interrupted.
    if current.get('description', '') == approval.description:
        approval.status = 'applied'
        return approval
    if current.get('status') == 'cancelled' or current.get('etag') != approval.etag:
        raise HTTPException(409, detail={'code': 'calendar_changed'})
    updated = await external(client, 'PATCH', event_url(event),
                             headers={**headers, 'If-Match': approval.etag},
                             params={'sendUpdates': 'none'}, json={'description': approval.description})
    await upsert_event(session, event.calendar_id, updated)
    approval.status = 'applied'
    return approval


async def telegram_call(settings, client, method, body):
    token = settings.telegram_bot_token.get_secret_value()
    if not token:
        raise HTTPException(503, detail={'code': 'telegram_not_configured'})
    result = await external(client, 'POST', f'https://api.telegram.org/bot{token}/{method}', json=body)
    if not result.get('ok'):
        raise HTTPException(503, detail={'code': 'telegram_unavailable'})
    return result.get('result')


async def telegram_link(row, settings, client):
    bot = await telegram_call(settings, client, 'getMe', {})
    code = secrets.token_urlsafe(24)
    save_state(row, {**row.data, 'telegram_link': digest(code),
                     'telegram_link_expires': (now()+timedelta(minutes=10)).isoformat()})
    return 'https://t.me/' + bot['username'] + '?start=' + code


async def poll_telegram(row, settings, client):
    if not settings.telegram_bot_token.get_secret_value():
        return
    updates = await telegram_call(settings, client, 'getUpdates',
                                  {'offset': row.data.get('telegram_offset', 0), 'timeout': 0, 'allowed_updates': ['message']})
    data = dict(row.data)
    for update in updates:
        data['telegram_offset'] = max(data.get('telegram_offset', 0), update['update_id']+1)
        message = update.get('message', {})
        text = message.get('text', '')
        if not text.startswith('/start ') or message.get('chat', {}).get('type') != 'private':
            continue
        code = text.split(' ', 1)[1].strip()
        if (data.get('telegram_link') and secrets.compare_digest(digest(code), data['telegram_link'])
                and datetime.fromisoformat(data['telegram_link_expires']) > now()):
            data['telegram_chat'] = str(message['chat']['id'])
            data.pop('telegram_link', None)
            data.pop('telegram_link_expires', None)
    save_state(row, data)


def public_status(row, settings):
    data = row.data
    return {
        'google_configured': bool(settings.google_client_id and settings.google_client_secret.get_secret_value()
                                  and settings.integration_encryption_key.get_secret_value()),
        'google_connected': bool(data.get('google_refresh')),
        'calendars': data.get('calendars', []), 'last_sync': data.get('last_sync'), 'sync_error': data.get('sync_error'),
        'telegram_configured': bool(settings.telegram_bot_token.get_secret_value()),
        'telegram_connected': bool(data.get('telegram_chat')),
        'notifications': NotificationSettings.model_validate(data.get('notifications', {})).model_dump(),
        'worker_heartbeat': data.get('worker_heartbeat'), 'worker_error': data.get('worker_error'),
    }
