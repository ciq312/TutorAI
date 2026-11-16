import { useState, type FormEvent } from 'react';
import { useCalendarInbox } from '../../hooks/useCalendarInbox';
import type { CalendarEvent } from '../../services/integrationApi';
import type { Student, Lesson } from '../../types';
import { ui } from '../ui/styles';
function EventCard({
  event,
  students,
  busy,
  onDecide,
}: {
  event: CalendarEvent;
  students: Student[];
  busy: boolean;
  onDecide: (
    id: string,
    body: {
      action: 'link' | 'ignore';
      student_id?: string;
      new_student?: { name: string };
      whole_series?: boolean;
    },
  ) => Promise<void>;
}) {
  const [target, setTarget] = useState(
    event.suggested_students.length === 1 ? event.suggested_students[0].id : '',
  );
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    void onDecide(event.id, {
      action: 'link',
      ...(target === 'new'
        ? { new_student: { name: String(data.get('name')).trim() } }
        : { student_id: target }),
      whole_series: data.has('series'),
    });
  }
  return (
    <article className="rounded-xl border border-line p-4">
      <h3 className="mt-0 text-sm">{event.title || 'Без названия'}</h3>
      <p className="text-xs text-muted">
        {event.starts_at
          ? new Date(event.starts_at).toLocaleString('ru-RU')
          : 'Событие на весь день'}{' '}
        · {event.calendar_mode === 'teaching' ? 'Календарь занятий' : 'Смешанный календарь'}
      </p>
      {event.decision === 'linked' ? (
        <p className="text-xs text-accent">Ученик привязан — занятие в расписании</p>
      ) : (
        <>
          {!!event.suggested_students.length && (
            <p className="text-xs text-accent">
              Возможное совпадение: {event.suggested_students.map((s) => s.name).join(', ')}
            </p>
          )}
          {event.starts_at && (
            <form onSubmit={submit}>
              <label>
                Кто занимается
                <select required value={target} onChange={(e) => setTarget(e.target.value)}>
                  <option value="">Выберите ученика</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                  <option value="new">Добавить нового ученика…</option>
                </select>
              </label>
              {target === 'new' && (
                <label>
                  Имя нового ученика
                  <input name="name" required maxLength={200} />
                </label>
              )}
              {event.series_id && (
                <label className="flex items-center gap-2">
                  <input className="w-auto" type="checkbox" name="series" />
                  Привязать всю серию занятий
                </label>
              )}
              <button className={ui.primary} disabled={busy || !target}>
                Привязать ученика
              </button>
            </form>
          )}
          <button
            className={ui.secondary + ' mt-3'}
            disabled={busy || event.decision === 'ignored'}
            onClick={() => void onDecide(event.id, { action: 'ignore' })}
          >
            {event.decision === 'ignored' ? 'Отмечено как личное' : 'Не занятие'}
          </button>
        </>
      )}
    </article>
  );
}
export function CalendarInbox({
  students,
  enabled,
  onImported,
}: {
  students: Student[];
  enabled: boolean;
  onImported: (student: Student, lesson: Lesson) => void;
}) {
  const vm = useCalendarInbox(enabled, onImported);
  const [filter, setFilter] = useState('pending');
  const pending = vm.events.filter((e) => e.decision === 'pending').length;
  if (!vm.events.length && !vm.error) return null;
  return (
    <section className={ui.panel + ' mb-5'}>
      <details open={pending > 0}>
        <summary>События Google Calendar · {pending} ожидают привязки</summary>
        <p className="text-xs text-muted">
          Личные встречи остаются событиями. После привязки к ученику появится занятие с материалами
          и уведомлениями.
        </p>
        {vm.error && (
          <p className={ui.error} role="alert">
            {vm.error}
          </p>
        )}
        <div className="mb-4 flex flex-wrap gap-3">
          <select
            className="w-auto"
            aria-label="События Google"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="pending">Новые</option>
            <option value="all">Все события</option>
            <option value="ignored">Личные</option>
          </select>
          <button className={ui.secondary} disabled={vm.busy} onClick={() => void vm.refresh()}>
            Синхронизировать
          </button>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {vm.events
            .filter((e) => filter === 'all' || e.decision === filter)
            .map((event) => (
              <EventCard
                key={event.id}
                event={event}
                students={students}
                busy={vm.busy}
                onDecide={vm.decide}
              />
            ))}
        </div>
      </details>
    </section>
  );
}
