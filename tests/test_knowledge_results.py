import io
import json
from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import select
from pypdf import PdfWriter

from app.db.models import KnowledgeDocument, KnowledgeChunk, NotificationDelivery, Lesson
from app.services.context import get_provider
from app.services.materials import get_llm
from app.services.knowledge import extract_pages, index_document
from app.services.integrations import state, save_state, now
from app.services.notifications import queue_notifications, valid_results
from test_integrations import db


class Embeddings:
    identity='test/library'
    dimensions=3
    def __init__(self):self.inputs=[]
    async def embed(self,texts,task):
        self.inputs.extend(texts)
        return [[1.,0.,0.] for _ in texts]


class ResultsLLM:
    def __init__(self):self.inputs=[]
    async def generate(self,system,prompt,schema):
        self.inputs.append(json.loads(prompt))
        return schema(facts=[],missing_data=[],summary='Разобрали уравнения [1]',homework='Решить x + 2 = 5',
                      teacher_answers='Ответ: x = 3',next_topic='Задачи',next_plan='Повторение 15 минут, практика 45 минут',
                      brief='Повторить уравнения и проверить ДЗ')


def upload(client,kind='curriculum',content='Квадратные уравнения. Дискриминант и задачи.'):
    response=client.post('/api/knowledge/documents',data={'title':'Учебный план','kind':kind},
                         files={'file':('plan.txt',content.encode(),'text/plain')})
    assert response.status_code==201,response.text
    return response.json()


def process(client,id,provider):
    async def run(session):await index_document(session,await session.get(KnowledgeDocument,UUID(id)),provider)
    db(client,run)


def records(client):
    student=client.post('/api/students',json={'name':'СекретноеИмя'}).json()
    lesson=client.post(f"/api/students/{student['id']}/lessons",json={'topic':'Уравнения',
        'scheduled_at':(now()-timedelta(hours=1)).isoformat(),'notes':'СекретноеИмя разобрал уравнения, email test@example.com'}).json()
    return student,lesson


def test_upload_background_index_page_sources_download_and_cascade(client):
    provider=Embeddings();client.app.dependency_overrides[get_provider]=lambda:provider
    records(client)
    doc=upload(client,content='СекретноеИмя: квадратные уравнения. test@example.com')
    assert doc['status']=='pending'
    process(client,doc['id'],provider)
    docs=client.get('/api/knowledge/documents').json()
    assert docs[0]['status']=='ready'
    result=client.post('/api/knowledge/search',json={'query':'Уравнения'})
    assert result.status_code==200,result.text
    source=result.json()[0]
    assert source['document_id']==doc['id'] and source['page']==1
    assert 'СекретноеИмя' not in source['text'] and 'test@example.com' not in source['text']
    assert all('СекретноеИмя' not in text and 'test@example.com' not in text for text in provider.inputs)
    assert 'СекретноеИмя' in client.get(f"/api/knowledge/documents/{doc['id']}/file").text
    assert client.delete(f"/api/knowledge/documents/{doc['id']}").status_code==204
    assert client.post('/api/knowledge/search',json={'query':'Уравнения'}).json()==[]


def test_curriculum_must_be_reviewed_before_assignment_and_progress_is_explicit(client):
    provider=Embeddings()
    student,lesson=records(client)
    doc=upload(client)
    process(client,doc['id'],provider)
    path=f"/api/students/{student['id']}/curriculum"
    assert client.put(path,json={'document_id':doc['id']}).status_code==422
    topics=[{'title':'Уравнения','page':1},{'title':'Задачи','page':1}]
    assert client.put(f"/api/knowledge/documents/{doc['id']}/topics",json={'topics':topics}).status_code==200
    assert client.put(path,json={'document_id':doc['id']}).status_code==200
    client.patch(f"/api/lessons/{lesson['id']}",json={'status':'completed'})
    assert client.get(path).json()['topic_index']==0
    assert client.put(path,json={'document_id':doc['id'],'topic_index':1}).json()['current_topic']['title']=='Задачи'
    assert client.put(f"/api/knowledge/documents/{doc['id']}/topics",json={'topics':topics[:1]}).status_code==409
    assert client.delete(f"/api/knowledge/documents/{doc['id']}").status_code==204
    assert client.get(path).json() is None


def test_results_review_persists_clean_homework_and_prevents_stale_approval(client):
    model=ResultsLLM();provider=Embeddings()
    client.app.dependency_overrides[get_llm]=lambda:model
    client.app.dependency_overrides[get_provider]=lambda:provider
    student,lesson=records(client)
    doc=upload(client)
    process(client,doc['id'],provider)
    client.put(f"/api/knowledge/documents/{doc['id']}/topics",json={'topics':[{'title':'Уравнения','page':1}]})
    client.put(f"/api/students/{student['id']}/curriculum",json={'document_id':doc['id']})
    generated=client.post(f"/api/lessons/{lesson['id']}/results/draft",json={})
    assert generated.status_code==200,generated.text
    draft=generated.json()
    assert not draft['approved'] and draft['knowledge_sources']
    assert client.get(f"/api/lessons/{lesson['id']}").json()['homework'] is None
    assert model.inputs[0]['curriculum']['current_topic']['title']=='Уравнения'
    assert 'СекретноеИмя' not in json.dumps(model.inputs[0],ensure_ascii=False)
    review={key:draft[key] for key in ['version','summary','homework','teacher_answers','next_topic','next_plan','brief']}
    accepted=client.put(f"/api/lessons/{lesson['id']}/results",json=review)
    assert accepted.status_code==200,accepted.text
    output=accepted.json()
    assert output['status']=='completed' and output['homework']==draft['homework']
    assert output['materials']['results']['approved']
    assert output['materials']['homework']['answers']=='Ответ: x = 3'
    assert 'Ответ' not in output['homework']
    # Repeating the same acceptance doesn't generate another result version.
    assert client.put(f"/api/lessons/{lesson['id']}/results",json=review).json()['materials']['results']['version']==draft['version']
    async def queue(session):
        row=await state(session);save_state(row,{**row.data,'telegram_chat':'123'})
        await queue_notifications(session,row,client.app.state.settings)
        return (await session.scalars(select(NotificationDelivery))).all()
    deliveries=db(client,queue)
    assert len(deliveries)==1 and deliveries[0].payload['kind']=='results'
    assert 'Ответ: x = 3' not in deliveries[0].payload['text']
    updated=client.put(f"/api/lessons/{lesson['id']}/homework",json={'homework':'Изменённое ДЗ'}).json()
    assert not updated['materials']['results']['approved']
    async def valid(session):return bool(valid_results(await session.get(Lesson,UUID(lesson['id']))))
    assert not db(client,valid)
    assert client.put(f"/api/lessons/{lesson['id']}/results",json=review).status_code==200
    client.patch(f"/api/lessons/{lesson['id']}",json={'notes':'Новые факты'})
    assert client.put(f"/api/lessons/{lesson['id']}/results",json=review).status_code==409


def test_results_without_notes_are_blocked_and_cancelled_lessons_not_generated(client):
    student,lesson=records(client)
    url=f"/api/lessons/{lesson['id']}"
    client.patch(url,json={'notes':None})
    assert client.post(url+'/results/draft',json={}).status_code==409
    client.patch(url,json={'notes':'Факты','status':'cancelled'})
    assert client.post(url+'/results/draft',json={}).status_code==409


def test_document_limits_and_pdf_without_text():
    writer=PdfWriter();writer.add_blank_page(width=200,height=200)
    data=io.BytesIO();writer.write(data)
    with pytest.raises(ValueError,match='pdf_needs_ocr'):extract_pages(data.getvalue(),'scan.pdf')
    with pytest.raises(ValueError,match='text_must_be_utf8'):extract_pages(b'\xff','bad.txt')


def test_unknown_or_wrong_documents_and_oversized_text(client):
    assert client.post('/api/knowledge/documents',data={'title':'Bad'},files={'file':('x.exe',b'x')}).status_code==422
    assert client.post('/api/knowledge/documents',data={'title':'Bad'},files={'file':('x.pdf',b'not a pdf')}).status_code==422
    assert client.post('/api/knowledge/documents',data={'title':' '},files={'file':('x.txt',b'x')}).status_code==422
