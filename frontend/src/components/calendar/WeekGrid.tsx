import { dayKey } from '../../utils/calendar';
import { LessonStatus } from '../lessons/LessonStatus';
import type { Lesson, Student } from '../../types';
type Props = {
  day: string;
  lessons: Lesson[];
  students: Student[];
  onDay: (day: string) => void;
  onOpen: (lesson: Lesson) => void;
};
export function WeekGrid({ day, lessons, students, onDay, onOpen }: Props) {
  const start = new Date(day + 'T12:00:00');
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
  const days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    return date;
  });
  const today = dayKey(new Date());
  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
      <div className="grid min-w-[700px] grid-cols-7">
        {days.map((date) => {
          const key = dayKey(date);
          const events = lessons.filter((l) => dayKey(new Date(l.scheduled_at)) === key);
          return (
            <div key={key} className="min-h-[400px] border-r border-line last:border-r-0">
              <button
                onClick={() => onDay(key)}
                className={`flex w-full items-center justify-center gap-2 border-b border-line py-4 text-[11px] ${key === day ? 'bg-[#393046] text-accent' : 'text-muted'}`}
              >
                <span>{date.toLocaleDateString('ru-RU', { weekday: 'short' })}</span>
                <span
                  className={`grid size-7 place-items-center rounded-lg ${key === today ? 'bg-primary text-primary-foreground' : ''}`}
                >
                  {date.getDate()}
                </span>
              </button>
              <div className="space-y-3 p-2">
                {events.map((lesson) => (
                  <button
                    key={lesson.id}
                    onClick={() => onOpen(lesson)}
                    className="w-full rounded-xl border border-[#51445f] bg-[#302939] p-3 text-left hover:border-accent"
                  >
                    <div className="mb-3 text-[10px] text-accent">
                      {new Date(lesson.scheduled_at).toLocaleTimeString('ru-RU', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}{' '}
                      · {lesson.duration_minutes || 60} мин
                    </div>
                    <strong className="block wrap-anywhere text-[11px]">
                      {students.find((s) => s.id === lesson.student_id)?.name}
                    </strong>
                    <p className="my-2 line-clamp-2 text-[10px] text-muted">{lesson.topic}</p>
                    <LessonStatus lesson={lesson} />
                  </button>
                ))}
                {!events.length && (
                  <p className="py-8 text-center text-[9px] text-[#626478]">Свободно</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
