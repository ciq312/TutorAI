from typing import Literal
from uuid import UUID
from urllib.parse import quote

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Response
from sqlalchemy import select, delete

from app.api.routes import Session, Provider, LLM
from app.db.models import KnowledgeDocument, CurriculumAssignment, Student
from app.schemas.knowledge import DocumentRead, KnowledgeSearch, CurriculumTopics, AssignmentInput, KnowledgeSource
from app.services.knowledge import search_library, draft_topics, curriculum_context
from app.services.records import require_record
from app.rag.embeddings import EmbeddingError

router = APIRouter(prefix='/api', tags=['Knowledge'])


@router.get('/knowledge/documents', response_model=list[DocumentRead])
async def documents(session: Session, limit: int = 100, offset: int = 0):
    if not 1 <= limit <= 100 or offset < 0:
        raise HTTPException(422)
    return (await session.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
                                  .limit(limit).offset(offset))).all()


@router.post('/knowledge/documents', response_model=DocumentRead, status_code=201)
async def upload(session: Session, file: UploadFile = File(), title: str = Form(),
                 kind: Literal['curriculum', 'textbook', 'method', 'own'] = Form('own')):
    filename = (file.filename or '').replace('\\', '/').split('/')[-1][:200]
    if not filename.lower().endswith(('.pdf', '.txt')) or not 1 <= len(title.strip()) <= 200:
        raise HTTPException(422, detail={'code': 'unsupported_document'})
    content = await file.read(15 * 1024 * 1024 + 1)
    await file.close()
    if not content or len(content) > 15 * 1024 * 1024:
        raise HTTPException(413, detail={'code': 'document_too_large'})
    if filename.lower().endswith('.pdf') and not content.startswith(b'%PDF-'):
        raise HTTPException(422, detail={'code': 'pdf_unreadable'})
    doc = KnowledgeDocument(title=title.strip(), filename=filename, kind=kind, content=content,
                             pages=[], topics=[], status='pending')
    session.add(doc)
    await session.flush()
    return doc


@router.get('/knowledge/documents/{document_id}/file')
async def download(document_id: UUID, session: Session):
    doc = await require_record(session, KnowledgeDocument, document_id)
    return Response(doc.content, media_type='application/pdf' if doc.filename.lower().endswith('.pdf') else 'text/plain',
                     headers={'Content-Disposition': "inline; filename*=UTF-8''" + quote(doc.filename, safe=''),
                              'X-Content-Type-Options': 'nosniff'})


@router.delete('/knowledge/documents/{document_id}', status_code=204)
async def delete_document(document_id: UUID, session: Session):
    doc = await session.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id == document_id).with_for_update())
    if not doc:
        raise HTTPException(404)
    await session.delete(doc)
    return Response(status_code=204)


@router.post('/knowledge/documents/{document_id}/reindex', response_model=DocumentRead)
async def reindex(document_id: UUID, session: Session):
    doc = await require_record(session, KnowledgeDocument, document_id)
    doc.status, doc.error = 'pending', None
    return doc


@router.post('/knowledge/search', response_model=list[KnowledgeSource])
async def search(data: KnowledgeSearch, session: Session, provider: Provider):
    try:
        return await search_library(session, data.query, provider, data.limit)
    except EmbeddingError:
        raise HTTPException(503, detail={'code': 'knowledge_search_unavailable'}) from None


@router.post('/knowledge/documents/{document_id}/topics/draft')
async def extract_curriculum(document_id: UUID, session: Session, llm: LLM):
    document = await require_record(session, KnowledgeDocument, document_id)
    if document.kind != 'curriculum':
        raise HTTPException(409, detail={'code': 'not_a_curriculum'})
    return await draft_topics(session, document, llm)


@router.put('/knowledge/documents/{document_id}/topics', response_model=DocumentRead)
async def save_topics(document_id: UUID, data: CurriculumTopics, session: Session):
    document = await session.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id == document_id).with_for_update())
    if not document:
        raise HTTPException(404)
    if document.kind != 'curriculum' or not document.pages or any(t.page > len(document.pages) for t in data.topics):
        raise HTTPException(422, detail={'code': 'invalid_curriculum_pages'})
    # Existing assignments retain their selected topic only when its position/title is unchanged.
    assignments = (await session.scalars(select(CurriculumAssignment).where(
        CurriculumAssignment.document_id == document_id))).all()
    updated = data.model_dump()['topics']
    for assignment in assignments:
        i = assignment.topic_index
        if i >= len(updated) or i >= len(document.topics) or updated[i]['title'] != document.topics[i]['title']:
            raise HTTPException(409, detail={'code': 'curriculum_in_use'})
    document.topics = updated
    return document


@router.get('/students/{student_id}/curriculum')
async def get_curriculum(student_id: UUID, session: Session):
    await require_record(session, Student, student_id)
    return await curriculum_context(session, student_id)


@router.put('/students/{student_id}/curriculum')
async def assign_curriculum(student_id: UUID, data: AssignmentInput, session: Session):
    await require_record(session, Student, student_id)
    document = await require_record(session, KnowledgeDocument, data.document_id)
    if document.kind != 'curriculum' or data.topic_index >= len(document.topics):
        raise HTTPException(422, detail={'code': 'curriculum_not_reviewed'})
    assignment = await session.get(CurriculumAssignment, student_id)
    if not assignment:
        assignment = CurriculumAssignment(student_id=student_id, document_id=document.id, topic_index=data.topic_index)
        session.add(assignment)
    else:
        assignment.document_id, assignment.topic_index = document.id, data.topic_index
    await session.flush()
    return await curriculum_context(session, student_id)


@router.delete('/students/{student_id}/curriculum', status_code=204)
async def unassign_curriculum(student_id: UUID, session: Session):
    await require_record(session, Student, student_id)
    await session.execute(delete(CurriculumAssignment).where(CurriculumAssignment.student_id == student_id))
    return Response(status_code=204)
