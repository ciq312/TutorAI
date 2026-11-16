"""Index lifecycle and student-scoped context retrieval."""
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunk, Lesson, Student
from app.rag.embeddings import EmbeddingError, EmbeddingProvider, validate_vectors
from app.rag.text import TEXT_VERSION, chunks, lesson_text
from app.schemas.context import ContextRequest
from app.services.records import require_record
from app.services.privacy import student_anonymizer


def get_provider(request: Request) -> EmbeddingProvider:
    return request.app.state.embedding_provider


async def index_lesson(session: AsyncSession, lesson: Lesson, provider: EmbeddingProvider) -> Lesson:
    # Callers serialize writes to this lesson using a row lock. A new lesson is
    # invisible to other transactions until the request transaction commits.
    await session.execute(delete(DocumentChunk).where(DocumentChunk.lesson_id == lesson.id))
    lesson.indexing_status = "pending"
    lesson.indexing_error = None
    student = await require_record(session, Student, lesson.student_id)
    texts = chunks(lesson_text(lesson, await student_anonymizer(session, student)))
    try:
        vectors = validate_vectors(
            await provider.embed(texts, "RETRIEVAL_DOCUMENT"), len(texts), provider.dimensions,
        )
    except EmbeddingError as exc:
        lesson.indexing_status = "failed"
        lesson.indexing_error = str(exc)
    else:
        session.add_all([
            DocumentChunk(student_id=lesson.student_id, lesson_id=lesson.id,
                          position=i, content=text, embedding=vector,
                          embedding_model=provider.identity, dimensions=provider.dimensions,
                          text_version=TEXT_VERSION)
            for i, (text, vector) in enumerate(zip(texts, vectors, strict=True))
        ])
        lesson.indexing_status = "ready"
    await session.flush()
    return lesson


async def locked_lesson(session: AsyncSession, lesson_id: UUID) -> Lesson:
    lesson = await session.scalar(select(Lesson).where(Lesson.id == lesson_id).with_for_update())
    if lesson is None:
        raise HTTPException(404, "Lesson not found")
    return lesson


async def search_context(session: AsyncSession, student_id: UUID, data: ContextRequest,
                         provider: EmbeddingProvider) -> dict:
    student = await require_record(session, Student, student_id)
    lessons = select(Lesson).where(Lesson.student_id == student_id, Lesson.status != "cancelled")
    if data.date_from is not None:
        lessons = lessons.where(Lesson.scheduled_at >= data.date_from)
    if data.date_to is not None:
        lessons = lessons.where(Lesson.scheduled_at <= data.date_to)
    anonymizer = await student_anonymizer(session, student)
    recent = list(await session.scalars(lessons.order_by(
        Lesson.scheduled_at.desc(), Lesson.id.desc(),
    ).limit(data.recent_lessons_limit)))

    eligible = lessons.with_only_columns(Lesson.id).where(Lesson.indexing_status == "ready")
    compatible = select(DocumentChunk).where(
        DocumentChunk.student_id == student_id,
        DocumentChunk.lesson_id.in_(eligible),
        DocumentChunk.embedding_model == provider.identity,
        DocumentChunk.dimensions == provider.dimensions,
        DocumentChunk.text_version == TEXT_VERSION,
    )
    indexed_lessons = compatible.with_only_columns(DocumentChunk.lesson_id).distinct()
    missing = await session.scalar(select(func.count()).select_from(
        lessons.where(Lesson.id.not_in(indexed_lessons)).subquery(),
    ))
    warnings = []
    if missing:
        warnings.append("index_incomplete")
    matches = []
    # Avoid quota usage for an empty index or chronology-only request.
    has_index = await session.scalar(select(compatible.exists()))
    semantic_status = "empty"
    if data.semantic_limit == 0:
        semantic_status = "disabled"
    elif has_index:
        try:
            vector = validate_vectors(await provider.embed(
                [anonymizer.prepare(data.query)], "RETRIEVAL_QUERY",
            ), 1, provider.dimensions)[0]
        except EmbeddingError as exc:
            semantic_status = "unavailable"
            warnings.append(str(exc))
        else:
            semantic_status = "ready"
            # Exact search is adequate for the MVP. Student/model/dimension
            # predicates are applied before distance ordering and LIMIT.
            distance = DocumentChunk.embedding.cosine_distance(vector)
            rows = await session.execute(compatible.with_only_columns(
                DocumentChunk, distance.label("distance"),
            ).order_by(distance, DocumentChunk.id).limit(data.semantic_limit))
            for chunk, value in rows:
                if value > data.max_distance:
                    continue
                matches.append({"lesson_id": chunk.lesson_id, "chunk_id": chunk.id,
                                "excerpt": chunk.content, "distance": float(value)})
    # A single lesson source can carry both reasons without duplicate excerpts.
    sources = {}
    for lesson in recent:
        sources[lesson.id] = {"lesson_id": lesson.id, "scheduled_at": lesson.scheduled_at,
                              "reasons": ["recent"], "excerpts": [lesson_text(lesson, anonymizer)],
                              "distance": None}
    for match in matches:
        lid = match["lesson_id"]
        if lid not in sources:
            lesson = await session.get(Lesson, lid)
            sources[lid] = {"lesson_id": lid, "scheduled_at": lesson.scheduled_at,
                            "reasons": ["semantic"], "excerpts": [], "distance": None}
        source = sources[lid]
        if "semantic" not in source["reasons"]:
            source["reasons"].append("semantic")
        if "recent" not in source["reasons"] and match["excerpt"] not in source["excerpts"]:
            source["excerpts"].append(match["excerpt"])
        source["distance"] = min(source["distance"] if source["distance"] is not None else 2,
                                 match["distance"])
    if not sources:
        warnings.append("no_context")
    # Bound returned context even for very long recent lessons.
    remaining = data.max_context_chars
    bounded = []
    for source in sources.values():
        excerpts = []
        for excerpt in source["excerpts"]:
            if remaining <= 0:
                break
            excerpts.append(excerpt[:remaining])
            remaining -= len(excerpts[-1])
        if excerpts:
            source["excerpts"] = excerpts
            bounded.append(source)
    if len(bounded) < len(sources) or remaining == 0:
        warnings.append("context_truncated")
    return {"student_id": student_id, "sources": bounded,
            "semantic_status": semantic_status, "unindexed_lessons": missing,
            "warnings": warnings}
