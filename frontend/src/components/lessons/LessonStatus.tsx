import type { Lesson } from '../../types';
import { lessonStatus } from '../../utils/lessonStatus';
export function LessonStatus({ lesson }: { lesson: Lesson }) {
  const status = lessonStatus(lesson);
  return (
    <span
      className={`inline-flex w-fit rounded-md px-2 py-1 text-[9px] font-semibold ${status.className}`}
    >
      {status.label}
    </span>
  );
}
