import { KnowledgeSources } from './KnowledgeSources';
import { useEffect, useState, type FormEvent } from 'react';
import { Check, Copy, Save, Sparkles, LoaderCircle } from 'lucide-react';
import { ui } from '../ui/styles';
import type { LessonDraft } from '../../types';
type Props = {
  draft: LessonDraft | null | undefined;
  kind: 'plan' | 'homework' | 'next_plan' | 'feedback';
  topic: string;
  duration: number;
  busy: boolean;
  accepted?: string | null;
  onGenerate: (options: {
    topic: string;
    duration: number;
    instructions: string;
    recipient: string;
  }) => Promise<void>;
  onSave: (draft: LessonDraft) => Promise<void>;
  onAccept?: (text: string) => Promise<void>;
  onCopy: (text: string) => void;
};
export function DraftEditor({
  draft,
  kind,
  topic,
  duration,
  busy,
  accepted,
  onGenerate,
  onSave,
  onAccept,
  onCopy,
}: Props) {
  const [text, setText] = useState(draft?.text || '');
  const [answers, setAnswers] = useState(draft?.answers || '');
  const [instructions, setInstructions] = useState('');
  useEffect(() => {
    setText(draft?.text || '');
    setAnswers(draft?.answers || '');
  }, [draft]);
  function generate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    void onGenerate({
      topic: String(data.get('topic') || topic),
      duration: Number(data.get('duration') || duration),
      instructions,
      recipient: String(data.get('recipient') || 'parent'),
    });
  }
  return (
    <div>
      <form onSubmit={generate} className="mb-6 rounded-xl border border-line bg-canvas/40 p-5">
        <div className="grid grid-cols-[1fr_130px] gap-4 max-[500px]:grid-cols-1">
          {kind === 'plan' || kind === 'next_plan' ? (
            <label>
              Тема урока
              <input key={topic} name="topic" required maxLength={500} defaultValue={topic} />
            </label>
          ) : kind === 'feedback' ? (
            <label>
              Кому адресован фидбек
              <select name="recipient">
                <option value="parent">Родителю</option>
                <option value="student">Ученику</option>
              </select>
            </label>
          ) : (
            <div className="py-3 text-[12px] text-muted">
              Закрепляем материал занятия и отмеченные трудности.
            </div>
          )}
          {kind !== 'feedback' && (
            <label>
              {kind === 'homework' ? 'На выполнение' : 'Длительность'}, мин
              <input
                type="number"
                name="duration"
                required
                min={kind === 'homework' ? 5 : 10}
                max={kind === 'homework' ? 180 : 240}
                defaultValue={duration}
              />
            </label>
          )}
        </div>
        <label>
          Пожелания репетитора
          <textarea
            maxLength={500}
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder={
              kind === 'homework'
                ? 'Например: пять номеров на знаки, два с подвохом, без дробей'
                : 'Что учесть или изменить в материале?'
            }
            className="min-h-[75px]"
          />
        </label>
        <button className={ui.primary} disabled={busy}>
          {busy ? (
            <LoaderCircle size={15} className="motion-safe:animate-spin" />
          ) : (
            <Sparkles size={15} />
          )}
          {draft ? 'Пересобрать с пожеланиями' : 'Подготовить черновик'}
        </button>
        <p className="mb-0 text-[9px] text-muted">
          Новая генерация заменит текущий черновик. Подготовка может занять до трёх минут.
        </p>
      </form>
      {draft ? (
        <>
          {!!draft.missing_data?.length && (
            <div className={ui.difficulty}>
              <strong>Чего не хватает</strong>
              {draft.missing_data.map((item, i) => (
                <p key={i}>{item}</p>
              ))}
            </div>
          )}
          {draft.warnings?.some((code) => code !== 'tutor_review_required') && (
            <p className={ui.difficulty}>
              Контекст может быть неполным. Проверьте источники и дополните заметки перед
              использованием материала.
            </p>
          )}
          <div className="mb-4 flex items-center justify-between">
            <h2>Черновик</h2>
            <span className="text-[10px] text-accent">Редактируется преподавателем</span>
          </div>
          {draft.brief && (
            <div className={ui.brief}>
              <h3>Бриф по ученику</h3>
              <p className="whitespace-pre-wrap">{draft.brief}</p>
            </div>
          )}
          <label>
            Материал
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              maxLength={20000}
              className="min-h-[330px] text-[13px] leading-8"
            />
          </label>
          {kind === 'homework' && (
            <details>
              <summary>Решения — только для преподавателя</summary>
              <textarea
                value={answers}
                onChange={(e) => setAnswers(e.target.value)}
                maxLength={20000}
                className="min-h-[180px]"
              />
            </details>
          )}
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              className={ui.secondary}
              disabled={busy || !text.trim()}
              onClick={() => void onSave({ ...draft, text, answers })}
            >
              <Save size={14} />
              Сохранить правки
            </button>
            <button className={ui.secondary} onClick={() => onCopy(text)}>
              <Copy size={14} />
              Копировать
            </button>
            {kind === 'homework' && onAccept && (
              <button
                className={ui.primary}
                disabled={busy || !text.trim() || text !== draft.text || answers !== draft.answers}
                onClick={() => void onAccept(text)}
              >
                <Check size={14} />
                {accepted === text ? 'ДЗ принято' : 'Принять ДЗ'}
              </button>
            )}
          </div>
          {kind === 'homework' && (text !== draft.text || answers !== draft.answers) && (
            <p className="text-[10px] text-muted">
              Сначала сохраните правки, затем примите домашнее задание.
            </p>
          )}
          <KnowledgeSources sources={draft.knowledge_sources} />
          <details className="mt-6">
            <summary>Источники · {draft.sources.length}</summary>
            {draft.sources.map((source, i) => (
              <div key={source.lesson_id} className="text-[11px] text-muted">
                <h3 className="text-accent">
                  [{i + 1}] {new Date(source.scheduled_at).toLocaleDateString('ru-RU')}
                </h3>
                {source.excerpts.map((excerpt, j) => (
                  <p key={j} className="whitespace-pre-wrap">
                    {excerpt}
                  </p>
                ))}
              </div>
            ))}
            {!draft.sources.length && (
              <p className="text-muted">
                Источники отсутствуют. Проверьте, достаточно ли данных для этого материала.
              </p>
            )}
          </details>
          <p className="text-[9px] text-muted">
            Ссылка на источник не гарантирует правильность утверждения. Проверьте факты и решения.
          </p>
        </>
      ) : (
        <div className={ui.empty}>
          <Sparkles />
          <h3>Здесь появится материал</h3>
          <p>Задайте параметры и пожелания — затем проверьте подготовленный черновик.</p>
        </div>
      )}
    </div>
  );
}
