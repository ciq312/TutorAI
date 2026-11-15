from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import AwareDatetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Contact, Lesson, Student
from app.db.session import get_session
from app.schemas.data import (
    ContactCreate, ContactPatch, ContactRead, LessonCreate, LessonPatch,
    LessonRead, StudentCreate, StudentPatch, StudentRead,
)
from app.rag.embeddings import EmbeddingProvider
from app.rag.llm import LLMProvider
from app.schemas.context import ContextRequest, ContextResponse
from app.services.context import get_provider, index_lesson, locked_lesson, search_context
from app.services.records import create_record, require_record, update_record

from app.schemas.materials import (
    PlanRequest, PlanResponse, HomeworkRequest, HomeworkResponse,
    FeedbackRequest, FeedbackResponse, AcceptHomework,
)
from app.services.materials import generate_material, get_llm

router = APIRouter(prefix="/api")
Session = Annotated[AsyncSession, Depends(get_session, scope="function")]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]
Provider = Annotated[EmbeddingProvider, Depends(get_provider)]
LLM = Annotated[LLMProvider, Depends(get_llm)]


@router.get("/students", response_model=list[StudentRead], tags=["Students"])
async def list_students(session: Session, limit: Limit = 50, offset: Offset = 0):
    result = await session.scalars(
        select(Student).order_by(Student.created_at.desc(), Student.id.desc())
        .limit(limit).offset(offset)
    )
    return result.all()


@router.post("/students", response_model=StudentRead, status_code=201, tags=["Students"])
async def create_student(data: StudentCreate, session: Session):
    return await create_record(session, Student, data)


@router.get("/students/{student_id}", response_model=StudentRead, tags=["Students"])
async def get_student(student_id: UUID, session: Session):
    return await require_record(session, Student, student_id)


@router.patch("/students/{student_id}", response_model=StudentRead, tags=["Students"])
async def patch_student(student_id: UUID, data: StudentPatch, session: Session):
    return await update_record(session, await require_record(session, Student, student_id), data)


@router.delete("/students/{student_id}", status_code=204, tags=["Students"])
async def delete_student(student_id: UUID, session: Session):
    await session.delete(await require_record(session, Student, student_id))
    return Response(status_code=204)


@router.get("/students/{student_id}/contacts", response_model=list[ContactRead], tags=["Contacts"])
async def list_contacts(student_id: UUID, session: Session, limit: Limit = 50, offset: Offset = 0):
    await require_record(session, Student, student_id)
    result = await session.scalars(
        select(Contact).where(Contact.student_id == student_id)
        .order_by(Contact.name, Contact.id).limit(limit).offset(offset)
    )
    return result.all()


@router.post("/students/{student_id}/contacts", response_model=ContactRead, status_code=201, tags=["Contacts"])
async def create_contact(student_id: UUID, data: ContactCreate, session: Session):
    await require_record(session, Student, student_id)
    return await create_record(session, Contact, data, student_id=student_id)


@router.get("/contacts/{contact_id}", response_model=ContactRead, tags=["Contacts"])
async def get_contact(contact_id: UUID, session: Session):
    return await require_record(session, Contact, contact_id)


@router.patch("/contacts/{contact_id}", response_model=ContactRead, tags=["Contacts"])
async def patch_contact(contact_id: UUID, data: ContactPatch, session: Session):
    return await update_record(session, await require_record(session, Contact, contact_id), data)


@router.delete("/contacts/{contact_id}", status_code=204, tags=["Contacts"])
async def delete_contact(contact_id: UUID, session: Session):
    await session.delete(await require_record(session, Contact, contact_id))
    return Response(status_code=204)


@router.get("/students/{student_id}/lessons", response_model=list[LessonRead], tags=["Lessons"])
async def list_lessons(
    student_id: UUID, session: Session, limit: Limit = 50, offset: Offset = 0,
    date_from: AwareDatetime | None = None, date_to: AwareDatetime | None = None,
):
    """Newest first. Date bounds are inclusive and must include a timezone."""
    await require_record(session, Student, student_id)
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")
    query = select(Lesson).where(Lesson.student_id == student_id)
    if date_from is not None:
        query = query.where(Lesson.scheduled_at >= date_from)
    if date_to is not None:
        query = query.where(Lesson.scheduled_at <= date_to)
    result = await session.scalars(
        query.order_by(Lesson.scheduled_at.desc(), Lesson.id.desc()).limit(limit).offset(offset)
    )
    return result.all()


@router.post("/students/{student_id}/lessons", response_model=LessonRead, status_code=201, tags=["Lessons"])
async def create_lesson(student_id: UUID, data: LessonCreate, session: Session, provider: Provider):
    await require_record(session, Student, student_id)
    lesson = await create_record(session, Lesson, data, student_id=student_id)
    return await index_lesson(session, lesson, provider)


@router.get("/lessons/{lesson_id}", response_model=LessonRead, tags=["Lessons"])
async def get_lesson(lesson_id: UUID, session: Session):
    return await require_record(session, Lesson, lesson_id)


@router.patch("/lessons/{lesson_id}", response_model=LessonRead, tags=["Lessons"])
async def patch_lesson(lesson_id: UUID, data: LessonPatch, session: Session, provider: Provider):
    lesson = await locked_lesson(session, lesson_id)
    changed = any(getattr(lesson, key) != value for key, value in data.model_dump(exclude_unset=True).items()
                  if key != "scheduled_at")
    await update_record(session, lesson, data)
    if changed:
        await index_lesson(session, lesson, provider)
    return lesson


@router.delete("/lessons/{lesson_id}", status_code=204, tags=["Lessons"])
async def delete_lesson(lesson_id: UUID, session: Session):
    await session.delete(await require_record(session, Lesson, lesson_id))
    return Response(status_code=204)


@router.post("/lessons/{lesson_id}/index", response_model=LessonRead, tags=["Context"])
async def reindex_lesson(lesson_id: UUID, session: Session, provider: Provider):
    """Retry a failed index or rebuild for the configured model."""
    return await index_lesson(session, await locked_lesson(session, lesson_id), provider)


@router.post("/students/{student_id}/context/search", response_model=ContextResponse, tags=["Context"])
async def context_search(student_id: UUID, data: ContextRequest, session: Session, provider: Provider):
    return await search_context(session, student_id, data, provider)


@router.post("/students/{student_id}/lesson-plan", response_model=PlanResponse, tags=["Materials"])
async def lesson_plan(student_id: UUID, data: PlanRequest, session: Session, provider: Provider, llm: LLM):
    return await generate_material(session, student_id, data, provider, llm, "plan")


@router.post("/lessons/{lesson_id}/homework/draft", response_model=HomeworkResponse, tags=["Materials"])
async def homework_draft(lesson_id: UUID, data: HomeworkRequest, session: Session, provider: Provider, llm: LLM):
    lesson = await require_record(session, Lesson, lesson_id)
    return await generate_material(session, lesson.student_id, data, provider, llm, "homework", lesson)


@router.put("/lessons/{lesson_id}/homework", response_model=LessonRead, tags=["Materials"])
async def accept_homework(lesson_id: UUID, data: AcceptHomework, session: Session, provider: Provider):
    """Save the tutor-reviewed text as assigned homework and refresh its index."""
    lesson = await locked_lesson(session, lesson_id)
    if lesson.homework != data.homework:
        lesson.homework = data.homework
        await index_lesson(session, lesson, provider)
    return lesson


@router.post("/lessons/{lesson_id}/feedback/draft", response_model=FeedbackResponse, tags=["Materials"])
async def feedback_draft(lesson_id: UUID, data: FeedbackRequest, session: Session, provider: Provider, llm: LLM):
    lesson = await require_record(session, Lesson, lesson_id)
    return await generate_material(session, lesson.student_id, data, provider, llm, "feedback", lesson)
