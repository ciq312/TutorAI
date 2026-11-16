import type { FormEvent } from 'react';
import type { Student } from '../../types';
import { ui } from '../ui/styles';
type Props = {
  student: Student;
  busy: boolean;
  error: string;
  saved: boolean;
  onSave: (e: FormEvent<HTMLFormElement>) => Promise<void>;
};
export function StudentProfileForm({ student, busy, error, saved, onSave }: Props) {
  return (
    <details className="mt-5">
      <summary>Редактировать профиль</summary>
      <form key={student.id} className="mt-4" onSubmit={onSave}>
        <label>
          Имя и фамилия
          <input name="name" required maxLength={200} defaultValue={student.name} />
        </label>
        <label>
          Класс или уровень
          <input name="grade" maxLength={100} defaultValue={student.grade || ''} />
        </label>
        <label>
          Цели и особенности обучения
          <textarea name="goals" maxLength={20000} defaultValue={student.goals || ''} />
        </label>
        {error && (
          <p role="alert" className={ui.error}>
            {error}
          </p>
        )}
        <button className={ui.secondary} disabled={busy}>
          Сохранить профиль
        </button>
        {saved && (
          <p role="status" className="text-[11px] text-accent">
            Профиль сохранён
          </p>
        )}
      </form>
    </details>
  );
}
