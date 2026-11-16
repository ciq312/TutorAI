import { useState } from 'react';
import { tutorApi } from '../services/tutorApi';
import type { Lesson, LessonDraft, Material, Student } from '../types';
export type LessonTab = 'plan' | 'outcomes' | 'homework' | 'student' | 'next_plan' | 'feedback';
type Options = {
  lesson: Lesson;
  student: Student;
  onCommit: (lesson: Lesson) => void;
};
export function useLessonWorkspace({ lesson, student, onCommit }: Options) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  async function patch(body: Partial<Lesson>): Promise<Lesson> {
    const updated = await tutorApi.updateLesson(lesson.id, body);
    onCommit(updated);
    return updated;
  }
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function save(body: Partial<Lesson>, message = 'Изменения сохранены') {
    return run(async () => {
      await patch(body);
      setNotice(message);
    });
  }
  function saveDraft(tab: 'plan' | 'homework' | 'next_plan' | 'feedback', draft: LessonDraft) {
    return save({ materials: { ...lesson.materials, [tab]: draft } }, 'Черновик сохранён');
  }
  function generate(
    tab: 'plan' | 'homework' | 'next_plan' | 'feedback',
    options: { topic: string; duration: number; instructions: string; recipient: string },
  ) {
    return run(async () => {
      if (lesson.status === 'cancelled')
        throw new Error('Занятие отменено. Восстановите его для подготовки материалов.');
      const result: Material = await tutorApi.generateMaterial(
        tab === 'plan' || tab === 'next_plan'
          ? {
              kind: 'plan',
              studentId: student.id,
              topic: options.topic,
              duration: options.duration,
              instructions: options.instructions,
            }
          : tab === 'homework'
            ? {
                kind: 'homework',
                lessonId: lesson.id,
                duration: options.duration,
                instructions: options.instructions,
              }
            : {
                kind: 'feedback',
                lessonId: lesson.id,
                recipient: options.recipient,
                instructions: options.instructions,
              },
      );
      const draft: LessonDraft = {
        knowledge_sources: result.knowledge_sources,
        missing_data: result.missing_data,
        warnings: result.warnings,
        text:
          (tab === 'homework'
            ? result.homework
            : tab === 'feedback'
              ? result.feedback
              : result.plan) || '',
        brief: result.brief || '',
        answers: result.teacher_answers || '',
        sources: result.sources.map(({ lesson_id, scheduled_at, excerpts }) => ({
          lesson_id,
          scheduled_at,
          excerpts,
        })),
      };
      await patch({
        materials: {
          ...lesson.materials,
          [tab]: draft,
          ...(tab === 'next_plan' ? { next_topic: options.topic } : {}),
        },
      });
      setNotice('Черновик подготовлен и сохранён. Проверьте его перед использованием.');
    });
  }
  function acceptHomework(text: string) {
    return run(async () => {
      if (!text.trim()) return;
      const updated = await tutorApi.saveHomework(lesson.id, text);
      onCommit(updated);
      setNotice('Домашнее задание принято. Версия для ученика готова.');
    });
  }
  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setNotice('Скопировано');
    } catch {
      setError('Не удалось скопировать. Выделите текст вручную.');
    }
  }
  return { busy, error, notice, save, saveDraft, generate, acceptHomework, copy };
}
