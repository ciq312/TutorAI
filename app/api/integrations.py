import secrets
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy import select

from app.api.routes import Session, Provider
from app.db.models import CalendarEvent, CalendarSeries, Student, CalendarApproval, Lesson
from app.schemas.data import LessonRead
from app.schemas.integrations import CalendarSettings, EventDecision, EventRead, NotificationSettings, ApprovalRead
from app.services import integrations as service
from app.services.records import require_record

router = APIRouter(prefix='/api/integrations', tags=['Integrations'])


def resources(request):
    return request.app.state.settings, request.app.state.integration_client


@router.get('/status')
async def status(session: Session, request: Request):
    settings, _ = resources(request)
    return service.public_status(await service.state(session, lock=False), settings)


@router.post('/google/connect')
async def connect_google(session: Session, request: Request, response: Response):
    settings, _ = resources(request)
    value, url = await service.begin_oauth(session, settings)
    response.set_cookie('tutor_google_state', value, max_age=600, httponly=True,
                        secure=settings.google_redirect_uri.startswith('https://'), samesite='lax',
                        path='/api/integrations/google/callback')
    return {'url': url}


@router.get('/google/callback')
async def google_callback(session: Session, request: Request, state: str = '', code: str = '', error: str = ''):
    settings, client = resources(request)
    cookie = request.cookies.get('tutor_google_state', '')
    if not state or not cookie or not secrets.compare_digest(state, cookie):
        raise HTTPException(400, detail={'code': 'oauth_state_invalid'})
    if error or not code:
        return HTMLResponse('<h1>Подключение отменено</h1><p>Вернитесь в настройки приложения.</p>', status_code=400)
    await service.complete_oauth(session, settings, client, state, code)
    response = RedirectResponse(settings.public_app_url, status_code=303)
    response.delete_cookie('tutor_google_state', path='/api/integrations/google/callback')
    return response


@router.delete('/google', status_code=204)
async def disconnect_google(session: Session):
    row = await service.state(session)
    service.save_state(row, {k: v for k, v in row.data.items()
                             if not k.startswith(('google_', 'oauth_')) and k not in {'calendars', 'last_sync', 'sync_error'}})
    return Response(status_code=204)


@router.get('/google/calendars')
async def calendars(session: Session, request: Request):
    return await service.calendar_list(await service.state(session), *resources(request))


@router.put('/google/calendars')
async def choose_calendars(data: CalendarSettings, session: Session, request: Request):
    row = await service.state(session)
    available = {c['id'] for c in await service.calendar_list(row, *resources(request))}
    if any(c.calendar_id not in available for c in data.calendars):
        raise HTTPException(422, detail={'code': 'unknown_calendar'})
    service.save_state(row, {**row.data, 'calendars': data.model_dump()['calendars'], 'last_sync': None})
    return {'saved': True}


@router.post('/google/sync')
async def sync(session: Session, request: Request):
    return {'events_processed': await service.sync_calendars(session, await service.state(session), *resources(request))}


@router.get('/google/events', response_model=list[EventRead])
async def events(session: Session, decision: str | None = None,
                 limit: int = Query(default=100, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    row = await service.state(session, lock=False)
    selected = {c['calendar_id']: c['mode'] for c in row.data.get('calendars', [])}
    query = select(CalendarEvent).where(CalendarEvent.calendar_id.in_(selected),
                                         CalendarEvent.status != 'cancelled')
    if decision:
        query = query.where(CalendarEvent.decision == decision)
    query = query.order_by(CalendarEvent.starts_at.asc().nullsfirst(), CalendarEvent.id).limit(limit).offset(offset)
    students = (await session.scalars(select(Student))).all()
    result = []
    for event in (await session.scalars(query)).all():
        item = EventRead.model_validate(event)
        title = event.title.casefold()
        item.suggested_students = [{'id': str(s.id), 'name': s.name} for s in students
                                   if s.name.casefold() in title]
        item.calendar_mode = selected[event.calendar_id]
        result.append(item)
    return result


@router.post('/google/events/{event_id}/decision')
async def decide_event(event_id: UUID, data: EventDecision, session: Session):
    row = await service.state(session)
    event = await require_record(session, CalendarEvent, event_id)
    if event.calendar_id not in {c['calendar_id'] for c in row.data.get('calendars', [])}:
        raise HTTPException(409, detail={'code': 'calendar_not_selected'})
    if data.action == 'ignore':
        if event.lesson_id:
            raise HTTPException(409, detail={'code': 'event_already_linked'})
        event.decision = 'ignored'
        return {'lesson': None, 'student': None}
    student = await require_record(session, Student, data.student_id) if data.student_id else Student(**data.new_student.model_dump())
    if not data.student_id:
        session.add(student)
        await session.flush()
    lesson = await service.attach(session, event, student.id)
    if data.whole_series and event.series_id:
        series = await session.scalar(select(CalendarSeries).where(
            CalendarSeries.calendar_id == event.calendar_id, CalendarSeries.external_id == event.series_id))
        if series and series.student_id != student.id:
            raise HTTPException(409, detail={'code': 'series_already_linked'})
        if not series:
            session.add(CalendarSeries(calendar_id=event.calendar_id, external_id=event.series_id, student_id=student.id))
        siblings = (await session.scalars(select(CalendarEvent).where(
            CalendarEvent.calendar_id == event.calendar_id, CalendarEvent.series_id == event.series_id,
            CalendarEvent.decision == 'pending', CalendarEvent.status != 'cancelled'))).all()
        for sibling in siblings:
            if sibling.starts_at and sibling.ends_at and 10 <= (sibling.ends_at-sibling.starts_at).total_seconds()/60 <= 240:
                await service.attach(session, sibling, student.id)
    from app.schemas.data import StudentRead
    return {'lesson': LessonRead.model_validate(lesson), 'student': StudentRead.model_validate(student)}


@router.post('/lessons/{lesson_id}/calendar-homework/preview', response_model=ApprovalRead)
async def preview(lesson_id: UUID, session: Session, request: Request):
    approval, event = await service.preview_homework(session, lesson_id, await service.state(session), *resources(request))
    return ApprovalRead.model_validate(approval).model_copy(update={'event_title': event.title, 'starts_at': event.starts_at})


@router.post('/calendar-approvals/{approval_id}/confirm', response_model=ApprovalRead)
async def confirm(approval_id: UUID, session: Session, request: Request):
    return await service.confirm_homework(session, approval_id, await service.state(session), *resources(request))


@router.delete('/calendar-approvals/{approval_id}', status_code=204)
async def cancel(approval_id: UUID, session: Session):
    await service.state(session)
    approval = await require_record(session, CalendarApproval, approval_id)
    if approval.status == 'pending':
        approval.status = 'cancelled'
    return Response(status_code=204)


@router.post('/telegram/connect')
async def connect_telegram(session: Session, request: Request):
    return {'url': await service.telegram_link(await service.state(session), *resources(request))}


@router.post('/telegram/check')
async def check_telegram(session: Session, request: Request):
    row = await service.state(session)
    await service.poll_telegram(row, *resources(request))
    return {'connected': bool(row.data.get('telegram_chat'))}


@router.delete('/telegram', status_code=204)
async def disconnect_telegram(session: Session):
    row = await service.state(session)
    service.save_state(row, {k: v for k, v in row.data.items() if k not in
                             {'telegram_chat', 'telegram_link', 'telegram_link_expires'}})
    return Response(status_code=204)


@router.put('/notifications')
async def notification_settings(data: NotificationSettings, session: Session):
    row = await service.state(session)
    service.save_state(row, {**row.data, 'notifications': data.model_dump()})
    return data


@router.get('/notifications/deliveries')
async def deliveries(session: Session):
    from app.db.models import NotificationDelivery
    rows = (await session.execute(select(NotificationDelivery, Student.name, Lesson.scheduled_at)
        .join(Lesson, Lesson.id == NotificationDelivery.lesson_id).join(Student, Student.id == Lesson.student_id)
        .order_by(Lesson.scheduled_at.desc(), NotificationDelivery.key.desc()).limit(50))).all()
    return [{'key': d.key, 'lesson_id': d.lesson_id, 'student_name': name, 'scheduled_at': scheduled_at,
             'kind': d.payload.get('kind'), 'status': d.status, 'attempts': d.attempts, 'error': d.error}
            for d, name, scheduled_at in rows]


from pydantic import BaseModel, Field

class RetryNotification(BaseModel):
    key: str = Field(min_length=1, max_length=250)


@router.post('/notifications/retry')
async def retry_delivery(data: RetryNotification, session: Session):
    from app.db.models import NotificationDelivery
    row = await service.state(session)
    delivery = await session.get(NotificationDelivery, data.key)
    if not delivery:
        raise HTTPException(404)
    if delivery.status not in {'uncertain', 'sending'}:
        raise HTTPException(409, detail={'code': 'delivery_not_retryable'})
    # A sending row can only be retried after a grace period (worker may still be sending).
    if delivery.retry_at and delivery.retry_at > service.now():
        raise HTTPException(409, detail={'code': 'delivery_still_sending'})
    from app.services.notifications import delivery_current
    lesson = await session.get(Lesson, delivery.lesson_id)
    if not delivery_current(delivery, lesson, row):
        raise HTTPException(409, detail={'code': 'notification_stale'})
    delivery.status, delivery.error = 'queued', None
    return {'queued': True}
