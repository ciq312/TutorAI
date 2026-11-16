import { useState, type FormEvent } from 'react';
import type { Preferences } from '../../hooks/usePreferences';
import { ui } from '../ui/styles';
export function AutomationSettings({
  preferences,
  onSave,
}: {
  preferences: Preferences;
  onSave: (value: Preferences) => void;
}) {
  const [saved, setSaved] = useState(false);
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    onSave({ ...preferences, preparationMinutes: Number(data.get('before')) });
    setSaved(true);
  }
  return (
    <section className={ui.panel}>
      <h2>Новые занятия</h2>
      <p className="text-xs text-muted">
        Время подготовки по умолчанию сохраняется на устройстве. Расписание сообщений Telegram
        настраивается отдельно ниже.
      </p>
      <form onSubmit={submit} onChange={() => setSaved(false)}>
        <label>
          Время на подготовку, минут
          <input
            name="before"
            type="number"
            required
            min={0}
            max={10080}
            defaultValue={preferences.preparationMinutes}
          />
        </label>
        <button className={ui.secondary}>Сохранить предпочтение</button>
        {saved && (
          <span role="status" className="ml-3 text-xs text-accent">
            Сохранено
          </span>
        )}
      </form>
    </section>
  );
}
