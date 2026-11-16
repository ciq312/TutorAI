import type { Lesson } from '../types';
export function lessonStatus(
  lesson: Lesson,
  now = new Date(),
): { label: string; className: string } {
  if (lesson.status === 'cancelled')
    return { label: 'Отменено', className: 'bg-[#413039] text-[#e2aebd]' };
  if (lesson.materials?.homework?.text && lesson.materials.homework.text !== lesson.homework)
    return { label: 'ДЗ на проверке', className: 'bg-[#493e2d] text-[#e5c58d]' };
  if (lesson.status === 'completed')
    return lesson.homework
      ? { label: 'Завершено', className: 'bg-[#293e37] text-[#a1d2bc]' }
      : { label: 'Итоги сохранены', className: 'bg-[#293e37] text-[#a1d2bc]' };
  if (new Date(lesson.scheduled_at) <= now)
    return { label: 'Ожидаются итоги', className: 'bg-[#493e2d] text-[#e5c58d]' };
  if (lesson.materials?.plan?.text)
    return { label: 'Подготовка готова', className: 'bg-[#3a304d] text-[#cbb5f3]' };
  return { label: 'Запланировано', className: 'bg-[#303644] text-[#adbdd5]' };
}
