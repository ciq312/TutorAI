import { useCallback, useEffect, useState } from 'react';
import {
  integrationApi,
  type KnowledgeDocument,
  type CurriculumTopic,
  type Curriculum,
} from '../services/integrationApi';
import type { KnowledgeSource } from '../types';
export function useKnowledge() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [searched, setSearched] = useState(false);
  const [editing, setEditing] = useState<KnowledgeDocument | null>(null);
  const [topics, setTopics] = useState<CurriculumTopic[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const load = useCallback(async () => setDocuments(await integrationApi.documents()), []);
  useEffect(() => {
    void load().catch((e) => setError(e.message));
  }, [load]);
  async function run(action: () => Promise<void>, message = '') {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
      setNotice(message);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return {
    documents,
    sources,
    searched,
    editing,
    topics,
    setTopics,
    busy,
    error,
    notice,
    refresh: () => run(load),
    upload: (file: File, title: string, kind: string) =>
      run(async () => {
        await integrationApi.upload(file, title, kind);
        await load();
      }, 'Документ загружен. Worker обработает его в фоне.'),
    remove: (id: string) =>
      run(async () => {
        await integrationApi.deleteDocument(id);
        if (editing?.id === id) setEditing(null);
        await load();
      }, 'Документ удалён'),
    reindex: (id: string) =>
      run(async () => {
        await integrationApi.reindex(id);
        await load();
      }, 'Поставлено в очередь'),
    search: (query: string) =>
      run(async () => {
        setSources(await integrationApi.search(query));
        setSearched(true);
      }),
    edit: (doc: KnowledgeDocument) => {
      setEditing(doc);
      setTopics(doc.topics.length ? doc.topics : [{ title: '', objectives: '', page: 1 }]);
      setError('');
    },
    close: () => setEditing(null),
    extract: () =>
      run(async () => {
        if (!editing) return;
        const draft = await integrationApi.extractTopics(editing.id);
        setTopics(draft.topics);
        setNotice(
          draft.truncated
            ? 'Обработана часть документа. Проверьте полноту тем.'
            : 'Темы извлечены. Проверьте и сохраните список.',
        );
      }),
    saveTopics: () =>
      run(async () => {
        if (!editing) return;
        await integrationApi.saveTopics(editing.id, topics);
        await load();
        setEditing(null);
      }, 'КТП проверен и сохранён'),
  };
}
export function useCurriculum(studentId: string, documents: KnowledgeDocument[]) {
  const [current, setCurrent] = useState<Curriculum | null>(null);
  const [documentId, setDocumentId] = useState('');
  const [topicIndex, setTopicIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  useEffect(() => {
    let active = true;
    setCurrent(null);
    setDocumentId('');
    setTopicIndex(0);
    if (studentId)
      void integrationApi
        .curriculum(studentId)
        .then((c) => {
          if (active) {
            setCurrent(c);
            setDocumentId(c?.document_id || '');
            setTopicIndex(c?.topic_index || 0);
          }
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    return () => {
      active = false;
    };
  }, [studentId]);
  const document = documents.find((d) => d.id === documentId);
  async function save(remove = false) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      if (remove) await integrationApi.unassign(studentId);
      else await integrationApi.assign(studentId, documentId, topicIndex);
      setCurrent(await integrationApi.curriculum(studentId));
      if (remove) {
        setDocumentId('');
        setTopicIndex(0);
      }
      setNotice('Сохранено');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return {
    current,
    documentId,
    setDocumentId,
    topicIndex,
    setTopicIndex,
    document,
    busy,
    error,
    notice,
    save,
  };
}
