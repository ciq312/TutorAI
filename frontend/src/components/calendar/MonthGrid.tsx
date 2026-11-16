import { dayKey, monthDays } from '../../utils/calendar';
import type { Lesson, Student } from '../../types';
type Props = {
  month: Date;
  selectedDay: string;
  lessons: Lesson[];
  students: Student[];
  onSelect: (day: string) => void;
};
export function MonthGrid({ month, selectedDay, lessons, students, onSelect }: Props) {
  const today = dayKey(new Date());
  const names = new Map(students.map((s) => [s.id, s.name]));
  const byDay = new Map<string, Lesson[]>();
  for (const lesson of lessons) {
    const key = dayKey(new Date(lesson.scheduled_at));
    byDay.set(key, [...(byDay.get(key) ?? []), lesson]);
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-surface">
      <div className="grid grid-cols-7 border-b border-line">
        {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((day) => (
          <div key={day} className="py-4 text-center text-[10px] font-bold text-muted">
            {day}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {monthDays(month).map((date) => {
          const key = dayKey(date);
          const events = byDay.get(key) ?? [];
          return (
            <button
              key={key}
              onClick={() => onSelect(key)}
              aria-label={`${date.toLocaleDateString('ru-RU')}, занятий: ${events.length}`}
              aria-pressed={selectedDay === key}
              className={`min-h-[105px] min-w-0 border-b border-r border-line p-2 text-left align-top hover:bg-[#332d42] max-[760px]:min-h-[72px] max-[760px]:p-1 ${selectedDay === key ? 'bg-[#332c44] ring-1 ring-inset ring-accent' : ''} ${date.getMonth() !== month.getMonth() ? 'opacity-40' : ''}`}
            >
              <span
                className={`mb-2 grid size-6 place-items-center rounded-lg text-[11px] ${today === key ? 'bg-primary text-primary-foreground' : 'text-[#ccc7da]'}`}
              >
                {date.getDate()}
              </span>
              <div className="space-y-1">
                {events.slice(0, 2).map((lesson) => (
                  <div
                    key={lesson.id}
                    className="truncate rounded bg-[#49405d] px-1.5 py-1 text-[8px] text-[#d3c3f2] max-[760px]:px-1"
                  >
                    <span className="max-[760px]:hidden">
                      {new Date(lesson.scheduled_at).toLocaleTimeString('ru-RU', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}{' '}
                    </span>
                    {names.get(lesson.student_id)}
                  </div>
                ))}
                {events.length > 2 && (
                  <span className="text-[8px] text-muted">+{events.length - 2}</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
