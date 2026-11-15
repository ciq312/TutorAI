"""Rebuild indexes one lesson/transaction at a time; stop on provider failure."""
import argparse
import asyncio
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models import DocumentChunk, Lesson
from app.rag.embeddings import build_provider
from app.rag.text import TEXT_VERSION
from app.services.context import index_lesson, locked_lesson


async def reindex(student_id: UUID | None = None, force: bool = False):
    config = get_settings()
    engine = create_async_engine(config.database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    counts = {"ready": 0, "failed": 0}
    try:
        async with httpx.AsyncClient(timeout=config.embedding_timeout) as client:
            provider = build_provider(config, client)
            async with factory() as session:
                query = select(Lesson.id).order_by(Lesson.id)
                if student_id:
                    query = query.where(Lesson.student_id == student_id)
                if not force:
                    compatible = select(DocumentChunk.id).where(
                        DocumentChunk.lesson_id == Lesson.id,
                        DocumentChunk.embedding_model == provider.identity,
                        DocumentChunk.dimensions == provider.dimensions,
                        DocumentChunk.text_version == TEXT_VERSION,
                    ).exists()
                    query = query.where((Lesson.indexing_status != "ready") | ~compatible)
                ids = list(await session.scalars(query))
            for lesson_id in ids:
                async with factory() as session, session.begin():
                    # A lesson can be deleted after the initial snapshot.
                    if await session.get(Lesson, lesson_id) is None:
                        continue
                    lesson = await locked_lesson(session, lesson_id)
                    await index_lesson(session, lesson, provider)
                    counts[lesson.indexing_status] += 1
                    error = lesson.indexing_error
                if error:
                    print(f"Stopped: {error}. Fix configuration/quota and rerun.")
                    break
    finally:
        await engine.dispose()
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-id", type=UUID)
    parser.add_argument("--force", action="store_true", help="Also rebuild compatible ready indexes")
    args = parser.parse_args()
    result = asyncio.run(reindex(args.student_id, args.force))
    print(result)
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
