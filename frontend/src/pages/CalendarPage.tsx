import { CalendarInbox } from '../components/calendar/CalendarInbox';
import { WeekGrid } from '../components/calendar/WeekGrid';
import { LessonStatus } from '../components/lessons/LessonStatus';
import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Plus, CalendarDays, LoaderCircle } from 'lucide-react';
import { ui } from '../components/ui/styles';
import { MonthGrid } from '../components/calendar/MonthGrid';
import { useCalendar } from '../hooks/useCalendar';
import { dayKey, isUpcoming } from '../utils/calendar';
import type { Student, Lesson } from '../types';
type Props = {
  onImported: (student: Student, lesson: Lesson) => void;
  students: Student[];
  selected: Student | null;
  enabled: boolean;
  revision: number;
  onCreate: (day: string) => void;
  onOpenLesson: (lesson: Lesson) => void;
};
export function CalendarPage({
  students,
  onImported,
  selected,
  enabled,
  revision,
  onCreate,
  onOpenLesson,
}: Props) {
  const [month, setMonth] = useState(() => new Date());
  const [day, setDay] = useState(() => dayKey(new Date()));
  const [view, setView] = useState<'week' | 'month'>('week');
  const [filter, setFilter] = useState('all');
  const [studentFilter, setStudentFilter] = useState('all');
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);
  const { lessons, loading, error } = useCalendar(students, enabled, revision);
  const filtered = lessons
    .filter(
      (l) =>
        (studentFilter === 'all' || l.student_id === studentFilter) &&
        (filter === 'all' || (filter === 'future') === isUpcoming(l.scheduled_at, now)),
    )
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());
  const dayLessons = filtered.filter((l) => dayKey(new Date(l.scheduled_at)) === day);
  function moveMonth(offset: number) {
    const next =
      view === 'month'
        ? new Date(month.getFullYear(), month.getMonth() + offset, 1)
        : new Date(day + 'T12:00:00');
    if (view === 'week') next.setDate(next.getDate() + offset * 7);
    setMonth(next);
    setDay(dayKey(next));
  }
  return (
    <>
      <div className={ui['page-heading']}>
        <div>
          <div className={ui.eyebrow}>ВРЕМЯ ДЛЯ ВАЖНОГО</div>
          <h1>Календарь занятий</h1>
          <p>Будущие встречи и история — на одной странице.</p>
        </div>
        <button className={ui.primary} disabled={!students.length} onClick={() => onCreate(day)}>
          <Plus size={16} />
          Добавить занятие
        </button>
      </div>
      <CalendarInbox students={students} enabled={enabled} onImported={onImported} />
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            className={ui['icon-btn']}
            onClick={() => moveMonth(-1)}
            aria-label="Предыдущий месяц"
          >
            <ChevronLeft size={18} />
          </button>
          <h2 className="min-w-[160px] capitalize">
            {month.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
          </h2>
          <button
            className={ui['icon-btn']}
            onClick={() => moveMonth(1)}
            aria-label="Следующий месяц"
          >
            <ChevronRight size={18} />
          </button>
          <button
            className="text-[10px] text-accent"
            onClick={() => {
              const today = new Date();
              setMonth(today);
              setDay(dayKey(today));
            }}
          >
            Сегодня
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="flex rounded-lg border border-line p-1">
            {(['week', 'month'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setView(mode)}
                className={`rounded-md px-3 py-1 text-[10px] ${view === mode ? 'bg-[#403252] text-accent' : 'text-muted'}`}
              >
                {mode === 'week' ? 'Неделя' : 'Месяц'}
              </button>
            ))}
          </div>
          <select
            aria-label="Ученик в календаре"
            value={studentFilter}
            onChange={(e) => setStudentFilter(e.target.value)}
            className="m-0 w-auto max-w-[200px] py-2 text-[10px]"
          >
            <option value="all">Все ученики</option>
            {students.map((s) => (
              <option value={s.id} key={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <select
            aria-label="Период занятий"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="m-0 w-auto py-2 text-[10px]"
          >
            <option value="all">Все занятия</option>
            <option value="future">Будущие</option>
            <option value="past">Прошедшие</option>
          </select>
        </div>
      </div>
      {error && (
        <p role="alert" className={ui.error}>
          {error}
        </p>
      )}
      {loading && (
        <p role="status" className="flex items-center gap-2 text-muted">
          <LoaderCircle size={15} className="motion-safe:animate-spin" />
          Загружаем занятия…
        </p>
      )}
      <div className="grid grid-cols-[minmax(0,1fr)_260px] gap-5 max-[1150px]:grid-cols-1">
        {view === 'week' ? (
          <WeekGrid
            day={day}
            lessons={filtered}
            students={students}
            onDay={setDay}
            onOpen={onOpenLesson}
          />
        ) : (
          <MonthGrid
            month={month}
            selectedDay={day}
            lessons={filtered}
            students={students}
            onSelect={setDay}
          />
        )}
        <aside className={ui.panel}>
          <div className="flex items-center gap-2 text-accent">
            <CalendarDays size={17} />
            <h2 className="text-[14px]">
              {new Date(day + 'T12:00:00').toLocaleDateString('ru-RU', {
                day: 'numeric',
                month: 'long',
              })}
            </h2>
          </div>
          {!dayLessons.length ? (
            <p className="text-[11px] text-muted">
              {loading
                ? 'Загружаем…'
                : 'На этот день занятий нет. Выберите другую дату или добавьте занятие.'}
            </p>
          ) : (
            dayLessons.map((l) => {
              const student = students.find((s) => s.id === l.student_id);
              const upcoming = isUpcoming(l.scheduled_at, now);
              return (
                <article key={l.id} className="mt-5 border-t border-line pt-4">
                  <div className="flex items-center justify-between text-[10px]">
                    <strong className="text-accent">
                      {new Date(l.scheduled_at).toLocaleTimeString('ru-RU', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </strong>
                    <span className={upcoming ? 'text-[#a6cdbb]' : 'text-muted'}>
                      {upcoming ? 'Предстоит' : 'Прошедшее'}
                    </span>
                  </div>
                  <div className="mt-3">
                    <LessonStatus lesson={l} />
                  </div>
                  <h3 className="mb-1 text-[13px]">{student?.name}</h3>
                  <p className="my-2 text-[11px] text-muted">{l.topic}</p>
                  {l.notes && <p className="text-[10px] text-muted">{l.notes}</p>}
                  {student && (
                    <button className="text-[10px] text-accent" onClick={() => onOpenLesson(l)}>
                      Открыть занятие →
                    </button>
                  )}
                </article>
              );
            })
          )}
        </aside>
      </div>
      <p className="mt-5 text-[9px] text-muted">
        Время показано в часовом поясе устройства. Сохраните итоги в карточке, чтобы отметить
        занятие проведённым.
        {!students.length && ' Добавьте ученика во вкладке «Ученики», чтобы назначить занятие.'}
      </p>
    </>
  );
}
