"""Persistent outbox. Ambiguous Telegram sends are surfaced for explicit retry."""
from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Lesson, Student, NotificationDelivery
from app.schemas.integrations import NotificationSettings
from app.services.integrations import now, digest
from app.services.results import results_basis


HOMEWORK_STATES = {'unknown': 'выполнение не отмечено', 'done': 'выполнено',
                   'partial': 'выполнено частично', 'not_done': 'не выполнено'}


def valid_results(lesson):
    results = lesson.materials.get('results') or {}
    return results if (results.get('approved') and results.get('based_on') == results_basis(lesson)
                       and results.get('homework') == lesson.homework) else {}


async def brief_text(session, lesson, student, timezone):
    previous = await session.scalar(select(Lesson).where(Lesson.student_id == student.id,
        Lesson.scheduled_at < lesson.scheduled_at, Lesson.status == 'completed')
        .order_by(Lesson.scheduled_at.desc(), Lesson.id).limit(1))
    plan = lesson.materials.get('plan') or {}
    result = valid_results(previous) if previous else {}
    text = plan.get('brief') or result.get('brief')
    if not text:
        text = ('Прошлый урок: ' + (previous.notes or previous.topic)[:900]) if previous else 'История предыдущих занятий отсутствует.'
    homework = previous.homework if previous else None
    status = HOMEWORK_STATES.get(previous.homework_status, HOMEWORK_STATES['unknown']) if previous else HOMEWORK_STATES['unknown']
    date = lesson.scheduled_at.astimezone(ZoneInfo(timezone)).strftime('%d.%m, %H:%M')
    # Fresh homework/status take precedence over the cached brief. Teacher answers are never included.
    return (f'Перед занятием — {student.name}\n{date} · {lesson.topic}\n\n{text[:1800]}\n\n'
            f'Предыдущее ДЗ: {(homework or "не задано")[:1100]}\nСтатус: {status}')


async def queue_notifications(session, row, settings):
    config = NotificationSettings.model_validate(row.data.get('notifications', {}))
    chat = row.data.get('telegram_chat')
    if not chat:
        return
    lessons = (await session.scalars(select(Lesson).where(
        Lesson.scheduled_at >= now()-timedelta(days=1), Lesson.scheduled_at <= now()+timedelta(days=8),
        Lesson.status != 'cancelled', Lesson.notifications_enabled.is_(True)))).all()
    for lesson in lessons:
        student = await session.get(Student, lesson.student_id)
        if not student:
            continue
        scheduled = lesson.scheduled_at
        entries = []
        if config.brief_enabled and lesson.status == 'scheduled' and scheduled-timedelta(minutes=config.before_minutes) <= now() < scheduled:
            entries.append(('brief:'+str(lesson.id)+':'+scheduled.isoformat(),
                            await brief_text(session, lesson, student, config.timezone), 'brief'))
        result = valid_results(lesson)
        if config.results_enabled and result and lesson.status == 'completed':
            text = (f'Итоги — {student.name}\n{lesson.topic}\n\n{result["summary"][:900]}\n\n'
                    f'ДЗ:\n{(lesson.homework or "не задано")[:1100]}\n\n'
                    f'Следующий урок: {result["next_topic"]}\n{result["next_plan"][:1400]}')
            entries.append(('results:'+str(lesson.id)+':'+result['version'], text, 'results'))
        reminder_at = scheduled+timedelta(minutes=lesson.duration_minutes+config.after_minutes)
        if config.reminder_enabled and lesson.status == 'scheduled' and reminder_at <= now() < reminder_at+timedelta(hours=6):
            entries.append(('reminder:'+str(lesson.id)+':'+scheduled.isoformat(),
                            f'Заполнить итоги — {student.name}\n{lesson.topic}\n'
                            'Время занятия закончилось. Если оно состоялось, сохраните заметки и сформируйте результаты.', 'reminder'))
        for key, text, kind in entries:
            await session.execute(insert(NotificationDelivery).values(
                key=key, lesson_id=lesson.id, status='queued', attempts=0,
                payload={'chat_id': chat, 'text': text[:4000], 'kind': kind,
                         'scheduled_at': scheduled.isoformat(), 'result_version': result.get('version'),
                         'url': settings.public_app_url.rstrip('/')+'/?lesson='+str(lesson.id)}
            ).on_conflict_do_nothing())


def delivery_current(delivery, lesson, row):
    if not lesson or lesson.status == 'cancelled' or not lesson.notifications_enabled:
        return False
    payload = delivery.payload
    if payload['chat_id'] != row.data.get('telegram_chat'):
        return False
    config = NotificationSettings.model_validate(row.data.get('notifications', {}))
    kind = payload['kind']
    if kind == 'results':
        return config.results_enabled and valid_results(lesson).get('version') == payload.get('result_version')
    if payload['scheduled_at'] != lesson.scheduled_at.isoformat() or lesson.status != 'scheduled':
        return False
    if kind == 'brief':
        return config.brief_enabled and lesson.scheduled_at-timedelta(minutes=config.before_minutes) <= now() < lesson.scheduled_at
    due = lesson.scheduled_at+timedelta(minutes=lesson.duration_minutes+config.after_minutes)
    return config.reminder_enabled and due <= now() < due+timedelta(hours=6)
