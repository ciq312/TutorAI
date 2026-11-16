import { type FormEvent } from 'react';
import { Check } from 'lucide-react';
import { ui } from '../ui/styles';
import type { Lesson } from '../../types';
type Props = {
  lesson: Lesson;
  busy: boolean;
  onSave: (body: Partial<Lesson>, message?: string) => Promise<void>;
};
export function OutcomesForm({ lesson, busy, onSave }: Props) {
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    void onSave(
      {
        notes: String(data.get('notes')).trim(),
        difficulties: String(data.get('difficulties')).trim() || null,
        status: 'completed',
        homework_status: String(data.get('homework_status')) as Lesson['homework_status'],
      },
      'Итоги сохранены. Можно составить домашнее задание',
    );
  }
  return (
    <form onSubmit={submit}>
      <h2>Что произошло на самом деле?</h2>
      <p className="text-[12px] text-muted">
        Эти заметки станут основой нового ДЗ, фидбека и следующего урока.
      </p>
      <label>
        Что прошли и как выполнено предыдущее ДЗ
        <textarea
          name="notes"
          required
          maxLength={20000}
          defaultValue={lesson.notes || ''}
          placeholder="Разобрали дискриминант. До Виета не дошли. В предыдущем ДЗ две ошибки со знаками…"
          className="min-h-[200px]"
        />
      </label>
      <label>
        Трудности и что стоит повторить
        <textarea
          name="difficulties"
          maxLength={20000}
          defaultValue={lesson.difficulties || ''}
          className="min-h-[100px]"
        />
      </label>
      <label>
        Статус ДЗ, заданного на этом занятии
        <select name="homework_status" defaultValue={lesson.homework_status || 'unknown'}>
          <option value="unknown">Не отмечено</option>
          <option value="done">Выполнено</option>
          <option value="partial">Частично</option>
          <option value="not_done">Не выполнено</option>
        </select>
      </label>
      <button className={ui.primary} disabled={busy}>
        <Check size={15} />
        Сохранить итоги и отметить проведённым
      </button>
    </form>
  );
}
