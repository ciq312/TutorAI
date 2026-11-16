import { useState, type FormEvent } from 'react';
import { useKnowledge, useCurriculum } from '../hooks/useKnowledge';
import type { KnowledgeDocument } from '../services/integrationApi';
import type { Student } from '../types';
import { ui } from '../components/ui/styles';
import { KnowledgeSources } from '../components/lessons/KnowledgeSources';
function CurriculumAssignment({
  students,
  documents,
}: {
  students: Student[];
  documents: KnowledgeDocument[];
}) {
  const [student, setStudent] = useState('');
  const vm = useCurriculum(student, documents);
  return (
    <section className={ui.panel}>
      <h2>КТП ученика</h2>
      <p className="text-xs text-muted">
        Выберите проверенный КТП и текущую тему. Переход к следующей теме подтверждает репетитор.
      </p>
      <label>
        Ученик
        <select value={student} onChange={(e) => setStudent(e.target.value)}>
          <option value="">Выберите ученика</option>
          {students.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
      {student && (
        <>
          <p className="text-xs text-accent">
            {vm.current
              ? `Сейчас: ${vm.current.title} · ${vm.current.current_topic.title}`
              : 'КТП пока не назначен'}
          </p>
          <label>
            Проверенный КТП
            <select
              value={vm.documentId}
              onChange={(e) => {
                vm.setDocumentId(e.target.value);
                vm.setTopicIndex(0);
              }}
            >
              <option value="">Выберите КТП</option>
              {documents
                .filter((d) => d.kind === 'curriculum' && d.topics.length > 0)
                .map((d) => (
                  <option value={d.id} key={d.id}>
                    {d.title}
                  </option>
                ))}
            </select>
          </label>
          {vm.document && (
            <label>
              Текущая тема
              <select
                value={vm.topicIndex}
                onChange={(e) => vm.setTopicIndex(Number(e.target.value))}
              >
                {vm.document.topics.map((t, i) => (
                  <option key={i} value={i}>
                    {i + 1}. {t.title}
                  </option>
                ))}
              </select>
            </label>
          )}
          <div className="flex gap-3">
            <button
              className={ui.primary}
              disabled={vm.busy || !vm.documentId}
              onClick={() => void vm.save()}
            >
              Назначить / обновить
            </button>
            {vm.current && (
              <button
                className={ui.secondary}
                disabled={vm.busy}
                onClick={() => void vm.save(true)}
              >
                Снять КТП
              </button>
            )}
          </div>
        </>
      )}
      {vm.error && (
        <p className={ui.error} role="alert">
          {vm.error}
        </p>
      )}
      {vm.notice && (
        <p className="text-accent" role="status">
          {vm.notice}
        </p>
      )}
    </section>
  );
}
export function KnowledgePage({ students }: { students: Student[] }) {
  const vm = useKnowledge();
  const [deleting, setDeleting] = useState('');
  function upload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const file = data.get('file');
    if (file instanceof File)
      void vm.upload(file, String(data.get('title')), String(data.get('kind')));
  }
  return (
    <>
      <div className={ui['page-heading']}>
        <div>
          <h1>База знаний</h1>
          <p>КТП, учебники и материалы, на которые опирается помощник.</p>
        </div>
        <button className={ui.secondary} disabled={vm.busy} onClick={() => void vm.refresh()}>
          Обновить статусы
        </button>
      </div>
      {vm.error && (
        <p className={ui.error} role="alert">
          {vm.error}
        </p>
      )}
      {vm.notice && (
        <p className="text-accent" role="status">
          {vm.notice}
        </p>
      )}
      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-5">
          <section className={ui.panel}>
            <h2>Найти материал</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void vm.search(String(new FormData(e.currentTarget).get('query')));
              }}
            >
              <label>
                Тема или задача
                <input
                  name="query"
                  required
                  maxLength={500}
                  placeholder="Упражнения на раскрытие скобок"
                />
              </label>
              <button disabled={vm.busy} className={ui.primary}>
                Найти
              </button>
            </form>
            <KnowledgeSources sources={vm.sources} />
            {vm.searched && !vm.sources.length && (
              <p className="text-xs text-muted">
                Совпадений нет. Проверьте, обработаны ли документы, или измените запрос.
              </p>
            )}
          </section>
          <section className={ui.panel}>
            <h2>Документы · {vm.documents.length}</h2>
            {!vm.documents.length && (
              <p className="text-sm text-muted">
                Загрузите первый документ. Для сканированных PDF потребуется предварительное
                распознавание текста.
              </p>
            )}
            {vm.documents.map((doc) => (
              <article className="my-4 rounded-xl border border-line p-4" key={doc.id}>
                <h3 className="mt-0 text-sm">{doc.title}</h3>
                <p className="text-xs text-muted">
                  {
                    (
                      {
                        curriculum: 'КТП',
                        textbook: 'Учебник',
                        method: 'Методика',
                        own: 'Свой материал',
                      } as Record<string, string>
                    )[doc.kind]
                  }{' '}
                  ·{' '}
                  {
                    (
                      {
                        pending: 'Ожидает обработки',
                        ready: 'Готов к поиску',
                        failed: 'Ошибка обработки',
                      } as Record<string, string>
                    )[doc.status]
                  }
                  {doc.kind === 'curriculum' &&
                    ` · ${doc.topics.length ? 'Темы проверены' : 'Темы ещё не проверены'}`}
                </p>
                {doc.error && (
                  <p className={ui.difficulty}>
                    {doc.error === 'pdf_needs_ocr'
                      ? 'В PDF нет доступного текста. Загрузите версию с распознанным текстом.'
                      : `Не удалось обработать документ (${doc.error}). Проверьте файл и настройки embeddings.`}
                  </p>
                )}
                <div className="flex flex-wrap gap-3">
                  <a
                    className={ui.secondary}
                    href={`/api/knowledge/documents/${doc.id}/file`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Открыть оригинал
                  </a>
                  {doc.kind === 'curriculum' && (
                    <button
                      className={ui.secondary}
                      disabled={vm.busy}
                      onClick={() => vm.edit(doc)}
                    >
                      Проверить темы КТП
                    </button>
                  )}
                  {doc.status !== 'pending' && (
                    <button
                      className={ui.secondary}
                      disabled={vm.busy}
                      onClick={() => void vm.reindex(doc.id)}
                    >
                      Переиндексировать
                    </button>
                  )}
                  <button
                    className={ui.secondary}
                    disabled={vm.busy}
                    onClick={() => setDeleting(doc.id)}
                  >
                    Удалить
                  </button>
                </div>
                {deleting === doc.id && (
                  <div className="mt-3 text-xs">
                    <p>Удалить документ, его индекс и назначения КТП ученикам?</p>
                    <button
                      className={ui.secondary}
                      disabled={vm.busy}
                      onClick={() => {
                        void vm.remove(doc.id);
                        setDeleting('');
                      }}
                    >
                      Подтвердить удаление
                    </button>
                    <button className={ui.secondary + ' ml-2'} onClick={() => setDeleting('')}>
                      Отмена
                    </button>
                  </div>
                )}
              </article>
            ))}
          </section>
          {vm.editing && (
            <section className={ui.panel}>
              <h2>Проверка КТП: {vm.editing.title}</h2>
              <p className="text-xs text-muted">
                Проверьте порядок, формулировки и страницы. Сохранённые темы можно назначать
                ученикам.
              </p>
              <button className={ui.secondary} disabled={vm.busy} onClick={() => void vm.extract()}>
                Извлечь темы с помощью ИИ
              </button>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void vm.saveTopics();
                }}
              >
                {vm.topics.map((t, i) => (
                  <fieldset className="my-4 rounded-xl border border-line p-4" key={i}>
                    <legend>Тема {i + 1}</legend>
                    <label>
                      Название
                      <input
                        required
                        maxLength={500}
                        value={t.title}
                        onChange={(e) =>
                          vm.setTopics((old) =>
                            old.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)),
                          )
                        }
                      />
                    </label>
                    <label>
                      Цели
                      <textarea
                        maxLength={20000}
                        value={t.objectives}
                        onChange={(e) =>
                          vm.setTopics((old) =>
                            old.map((x, j) => (j === i ? { ...x, objectives: e.target.value } : x)),
                          )
                        }
                      />
                    </label>
                    <label>
                      Страница источника
                      <input
                        type="number"
                        min={1}
                        max={500}
                        required
                        value={t.page}
                        onChange={(e) =>
                          vm.setTopics((old) =>
                            old.map((x, j) =>
                              j === i ? { ...x, page: Number(e.target.value) } : x,
                            ),
                          )
                        }
                      />
                    </label>
                    <button
                      type="button"
                      className={ui.secondary}
                      disabled={vm.topics.length === 1}
                      onClick={() => vm.setTopics((old) => old.filter((_, j) => i !== j))}
                    >
                      Убрать тему
                    </button>
                  </fieldset>
                ))}
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={vm.topics.length >= 200}
                    className={ui.secondary}
                    onClick={() =>
                      vm.setTopics((old) => [...old, { title: '', objectives: '', page: 1 }])
                    }
                  >
                    Добавить тему
                  </button>
                  <button className={ui.primary} disabled={vm.busy}>
                    Темы проверены — сохранить
                  </button>
                  <button type="button" className={ui.secondary} onClick={vm.close}>
                    Закрыть
                  </button>
                </div>
              </form>
            </section>
          )}
        </div>
        <aside className="space-y-5">
          <section className={ui.panel}>
            <h2>Загрузить документ</h2>
            <form onSubmit={upload}>
              <label>
                Название
                <input name="title" required maxLength={200} />
              </label>
              <label>
                Тип
                <select name="kind">
                  <option value="curriculum">КТП</option>
                  <option value="textbook">Учебник / сборник</option>
                  <option value="method">Методический материал</option>
                  <option value="own">Свой материал</option>
                </select>
              </label>
              <label>
                Файл до 15 МБ
                <input type="file" accept=".pdf,.txt" name="file" required />
              </label>
              <p className="text-xs text-muted">
                PDF с текстовым слоем или TXT в UTF-8. Индексация выполняется worker в фоне. При
                облачном провайдере текст передаётся ему для получения embeddings.
              </p>
              <button className={ui.primary} disabled={vm.busy}>
                Загрузить
              </button>
            </form>
          </section>
          <CurriculumAssignment students={students} documents={vm.documents} />
        </aside>
      </div>
    </>
  );
}
