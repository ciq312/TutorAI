import { ui } from '../ui/styles';
import { BookOpen, FileText, Clock3 } from 'lucide-react';
import type { Lesson } from '../../types';
import type { LessonTab } from '../../hooks/useLessonWorkspace';
import { formatDate as date } from '../../utils/format';
type Props = {
  onOpen: (lesson: Lesson, tab?: LessonTab) => void;
  lesson: Lesson;
};
export function LessonCard({ lesson: l, onOpen }: Props) {
  return (
    <article className="p-[23px_0] border-t border-line [&_h3]:text-[17px] [&_h3]:m-[12px_0] [&_p]:text-[12px] [&_p]:text-[#b7b4c9] [&_p]:wrap-anywhere">
      <span className="flex items-center gap-[7px] text-[#8e8da5] text-[10px]">
        <Clock3 size={14} />
        {date(l.scheduled_at)}
      </span>
      <h3>{l.topic}</h3>
      {onOpen && (
        <button className="text-[11px] text-accent" onClick={() => onOpen(l)}>
          Открыть карточку занятия →
        </button>
      )}
      <p>{l.notes || 'Заметки пока не добавлены'}</p>
      {l.difficulties && (
        <div className={ui['difficulty']}>На что обратить внимание: {l.difficulties}</div>
      )}
      {l.homework && (
        <details>
          <summary>Заданное домашнее задание</summary>
          <p className="whitespace-pre-wrap">{l.homework}</p>
        </details>
      )}
      <div className={ui['lesson-actions']}>
        <button className={ui['secondary']} onClick={() => onOpen(l, 'homework')}>
          <BookOpen size={15} />
          Составить ДЗ
        </button>
        <button className={ui['secondary']} onClick={() => onOpen(l, 'feedback')}>
          <FileText size={15} />
          Обратная связь
        </button>
      </div>
    </article>
  );
}
