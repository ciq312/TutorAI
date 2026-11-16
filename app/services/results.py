"""One reviewed result drives the lesson workspace and Telegram copy."""
import json
from uuid import uuid4
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from app.services.integrations import digest
from app.services.materials import generate_material


def results_basis(lesson):
    return digest(json.dumps([lesson.topic, lesson.notes, lesson.difficulties], ensure_ascii=False))


async def generate_results(session, lesson, data, embeddings, llm):
    if lesson.status == 'cancelled' or not (lesson.notes or '').strip():
        raise HTTPException(409, detail={'code': 'lesson_notes_required'})
    output = await generate_material(session, lesson.student_id, data, embeddings, llm, 'results', lesson)
    output = jsonable_encoder(output)
    output.update(version=str(uuid4()), approved=False, based_on=results_basis(lesson))
    lesson.materials = {**lesson.materials, 'results': output}
    return output


def accept_results(lesson, data):
    existing = lesson.materials.get('results') or {}
    if (str(data.version) != existing.get('version') or existing.get('based_on') != results_basis(lesson)
            or lesson.status == 'cancelled'):
        raise HTTPException(409, detail={'code': 'results_stale'})
    output = {**existing, **data.model_dump(mode='json'), 'approved': True}
    if existing.get('approved') and any(output.get(k) != existing.get(k) for k in data.model_fields_set):
        output['version'] = str(uuid4())
    sources = [{k: s[k] for k in ('lesson_id', 'scheduled_at', 'excerpts')} for s in output.get('sources', [])]
    draft = {'text': output['next_plan'], 'brief': output['brief'], 'answers': '', 'sources': sources,
             'knowledge_sources': output.get('knowledge_sources', [])}
    homework = {'text': output['homework'], 'answers': output['teacher_answers'], 'brief': '', 'sources': sources,
                'knowledge_sources': output.get('knowledge_sources', [])}
    lesson.materials = {**lesson.materials, 'results': output, 'next_plan': draft,
                        'next_topic': output['next_topic'], 'homework': homework}
    lesson.homework = output['homework']
    lesson.homework_status = 'unknown'
    lesson.status = 'completed'
    return lesson
