import { useState, useEffect, type FormEvent } from 'react';
import type { Lesson, ResultsDraft } from '../../types';
import { useLessonIntegrations } from '../../hooks/useLessonIntegrations';
import { KnowledgeSources } from './KnowledgeSources';
import { ui } from '../ui/styles';
export function ResultsEditor({
  lesson,
  onCommit,
}: {
  lesson: Lesson;
  onCommit: (lesson: Lesson) => void;
}) {
  const vm = useLessonIntegrations(lesson, onCommit);
  const stored = lesson.materials?.results;
  const [draft, setDraft] = useState<ResultsDraft | null>(stored || null);
  useEffect(() => setDraft(stored || null), [stored]);
  const fields = [
    ['summary', 'Краткая выжимка'],
    ['homework', 'Предлагаемое ДЗ'],
    ['next_topic', 'Тема следующего урока'],
    ['next_plan', 'Предлагаемый план следующего урока'],
    ['brief', 'Бриф перед следующим занятием'],
  ] as const;
  function submit(e: FormEvent) {
    e.preventDefault();
    if (draft) void vm.accept(draft);
  }
  return (
    <section className="mt-7 border-t border-line pt-6">
      <h2>Результаты и следующий шаг</h2>
      <p className="text-xs text-muted">
        ИИ использует сохранённые заметки, историю и назначенный КТП. Генерация создаёт черновик.
        Принятие сохраняет ДЗ, план и сообщение для Telegram.
      </p>
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
      <button
        className={ui.primary}
        disabled={vm.busy || !lesson.notes || lesson.status === 'cancelled'}
        onClick={() => void vm.generate()}
      >
        {vm.busy
          ? 'Подготавливаем…'
          : draft
            ? 'Сформировать заново'
            : 'Сформировать результаты занятия'}
      </button>
      {!lesson.notes && (
        <p className="text-xs text-muted">Сначала сохраните фактические итоги выше.</p>
      )}
      {draft && (
        <form onSubmit={submit}>
          <p className="mt-5 text-xs text-accent">
            {draft.approved ? 'Результаты приняты' : 'Черновик — требуется проверка'}
          </p>
          {!!draft.missing_data?.length && (
            <div className={ui.difficulty}>
              {draft.missing_data.map((text, i) => (
                <p key={i}>{text}</p>
              ))}
            </div>
          )}
          {draft.warnings?.includes('curriculum_not_assigned') && (
            <p className={ui.difficulty}>
              КТП не назначен. Предложение следующего урока основано на истории.
            </p>
          )}
          {fields.map(([key, label]) => (
            <label key={key}>
              {label}
              <textarea
                value={draft[key]}
                maxLength={key === 'next_topic' ? 500 : 20000}
                required
                className={key === 'next_plan' ? 'min-h-52' : 'min-h-24'}
                onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
              />
            </label>
          ))}
          <details>
            <summary>Решения — только для преподавателя</summary>
            <textarea
              maxLength={20000}
              value={draft.teacher_answers}
              onChange={(e) => setDraft({ ...draft, teacher_answers: e.target.value })}
            />
          </details>
          <KnowledgeSources sources={draft.knowledge_sources} />
          <details className="my-4">
            <summary>Источники истории · {draft.sources.length}</summary>
            {draft.sources.map((s, i) => (
              <div key={s.lesson_id} className="text-xs text-muted">
                <p>
                  [{i + 1}] {new Date(s.scheduled_at).toLocaleDateString('ru-RU')}
                </p>
                {s.excerpts.map((text, j) => (
                  <p className="whitespace-pre-wrap" key={j}>
                    {text}
                  </p>
                ))}
              </div>
            ))}
          </details>
          <button className={ui.primary} disabled={vm.busy || lesson.status === 'cancelled'}>
            Принять результаты и сохранить ДЗ
          </button>
          <p className="text-xs text-muted">
            В Telegram для репетитора попадут выжимка, принятое ДЗ и следующий план. Ответы к
            задачам в сообщение не включаются. Запись в Google Calendar подтверждается отдельно.
          </p>
        </form>
      )}
    </section>
  );
}
