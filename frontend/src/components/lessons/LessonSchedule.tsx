import { DateTimePicker } from '../ui/DateTimePicker';
import { type FormEvent } from 'react';
import { Save } from 'lucide-react';
import { ui } from '../ui/styles';
import type { Lesson } from '../../types';
export function LessonSchedule({
  lesson,
  busy,
  onSave,
}: {
  lesson: Lesson;
  busy: boolean;
  onSave: (body: Partial<Lesson>, message?: string) => Promise<void>;
}) {
  const local = new Date(
    new Date(lesson.scheduled_at).getTime() -
      new Date(lesson.scheduled_at).getTimezoneOffset() * 60000,
  )
    .toISOString()
    .slice(0, 16);
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    void onSave({
      topic: String(data.get('topic')),
      scheduled_at: new Date(String(data.get('date'))).toISOString(),
      duration_minutes: Number(data.get('duration')),
      preparation_minutes: Number(data.get('lead')),
    });
  }
  return (
    <details className="mt-5">
      <summary>Изменить время, тему и параметры</summary>
      <form key={lesson.scheduled_at} onSubmit={submit} className="mt-4">
        <label>
          Тема
          <input name="topic" required maxLength={500} defaultValue={lesson.topic} />
        </label>
        <label>
          Дата и время
          <DateTimePicker name="date" required defaultValue={local} disabled={busy} />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label>
            Длительность, мин
            <input
              name="duration"
              type="number"
              required
              min={10}
              max={240}
              defaultValue={lesson.duration_minutes || 60}
            />
          </label>
          <label>
            Время на подготовку, мин
            <input
              name="lead"
              type="number"
              required
              min={0}
              max={10080}
              defaultValue={lesson.preparation_minutes ?? 30}
            />
          </label>
        </div>
        <p className="text-[9px] text-muted">
          Время сообщений Telegram задаётся в настройках. Если занятие связано с Google, переносите
          его в Google: синхронизация обновит время здесь.
        </p>
        <button className={ui.secondary} disabled={busy}>
          <Save size={14} />
          Сохранить
        </button>
      </form>
      <button
        className="mt-5 text-[11px] text-[#e5a9ba]"
        disabled={busy}
        onClick={() =>
          void onSave(
            { status: lesson.status === 'cancelled' ? 'scheduled' : 'cancelled' },
            lesson.status === 'cancelled' ? 'Занятие восстановлено' : 'Занятие отменено',
          )
        }
      >
        {lesson.status === 'cancelled' ? 'Восстановить занятие' : 'Отменить занятие'}
      </button>
    </details>
  );
}
