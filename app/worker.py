"""Run separately: python -m app.worker. No background work is tied to browser lifetime."""
import asyncio
import logging

import httpx
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.db.models import IntegrationState, KnowledgeDocument, NotificationDelivery, Lesson
from app.rag.embeddings import build_provider
from app.services.integrations import state, save_state, now, sync_calendars, poll_telegram, telegram_call
from app.services.knowledge import index_document
from app.services.notifications import queue_notifications, delivery_current
from app.services.context import index_lesson

logger = logging.getLogger('tutor.worker')


async def integration_tick(factory, settings, client):
    async with factory() as session, session.begin():
        row = await state(session)
        error = None
        try:
            async with session.begin_nested():
                await poll_telegram(row, settings, client)
        except HTTPException:
            row = await state(session)
            error = 'telegram_poll_failed'
        save_state(row, {**row.data, 'worker_heartbeat': now().isoformat(), 'worker_error': error})
    async with factory() as session, session.begin():
        row = await state(session)
        if row.data.get('google_refresh') and row.data.get('calendars'):
            from datetime import datetime, timedelta
            last = row.data.get('last_sync')
            if not last or datetime.fromisoformat(last) < now()-timedelta(minutes=5):
                try:
                    async with session.begin_nested():
                        await sync_calendars(session, row, settings, client)
                except HTTPException as exc:
                    row = await state(session)
                    save_state(row, {**row.data, 'sync_error': exc.detail.get('code', 'integration_unavailable')})


async def document_tick(factory, provider):
    async with factory() as session, session.begin():
        document = await session.scalar(select(KnowledgeDocument).where(KnowledgeDocument.status == 'pending')
            .order_by(KnowledgeDocument.created_at).with_for_update(skip_locked=True).limit(1))
        if document:
            await index_document(session, document, provider)
    async with factory() as session, session.begin():
        lesson = await session.scalar(select(Lesson).where(Lesson.indexing_status == 'pending')
            .order_by(Lesson.scheduled_at.desc()).with_for_update(skip_locked=True).limit(1))
        if lesson:
            await index_lesson(session, lesson, provider)


async def notification_tick(factory, settings, client):
    async with factory() as session, session.begin():
        row = await state(session)
        await queue_notifications(session, row, settings)
    # Persist the sending state BEFORE contacting Telegram. A crash/timeout cannot silently resend.
    for _ in range(20):
        async with factory() as session, session.begin():
            delivery = await session.scalar(select(NotificationDelivery).where(NotificationDelivery.status == 'queued')
                                           .with_for_update(skip_locked=True).limit(1))
            if not delivery:
                return
            row = await state(session)
            lesson = await session.get(Lesson, delivery.lesson_id)
            if not delivery_current(delivery, lesson, row):
                delivery.status = 'cancelled'
                continue
            from datetime import timedelta
            delivery.retry_at = now()+timedelta(minutes=2)
            delivery.status, delivery.attempts = 'sending', delivery.attempts+1
            payload, key = dict(delivery.payload), delivery.key
        try:
            markup = None
            if payload['url'].startswith('https://'):
                markup = {'inline_keyboard': [[{'text': 'Открыть занятие', 'url': payload['url']}]]}
            body = {'chat_id': payload['chat_id'], 'text': payload['text']}
            if markup:
                body['reply_markup'] = markup
            await telegram_call(settings, client, 'sendMessage', body)
            status, error = 'sent', None
        except HTTPException:
            status, error = 'uncertain', 'telegram_delivery_unconfirmed'
        async with factory() as session, session.begin():
            delivery = await session.get(NotificationDelivery, key)
            if delivery:
                delivery.status, delivery.error = status, error


async def run():
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    # Telegram embeds its secret in the request path. Never log HTTP request URLs.
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        # One active poller avoids conflicting getUpdates consumers, even with accidental duplicate workers.
        async with engine.connect() as leader:
            if not await leader.scalar(text('SELECT pg_try_advisory_lock(80421691)')):
                raise RuntimeError('A tutor worker is already running')
            async with httpx.AsyncClient(timeout=30) as client:
                provider = build_provider(settings, client)
                while True:
                    for name, task in [('integrations', lambda: integration_tick(factory, settings, client)),
                                       ('documents', lambda: document_tick(factory, provider)),
                                       ('notifications', lambda: notification_tick(factory, settings, client))]:
                        try:
                            await task()
                        except Exception:
                            # No exception bodies: external HTTP errors can contain credential-bearing URLs.
                            logger.error('Worker task failed: %s', name)
                            async with factory() as session, session.begin():
                                row = await state(session)
                                save_state(row, {**row.data, 'worker_heartbeat': now().isoformat(),
                                                 'worker_error': name+'_failed'})
                    await asyncio.sleep(settings.worker_interval_seconds)
    finally:
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(run())
