import { useState } from 'react';
import { integrationApi, type CalendarApproval } from '../services/integrationApi';
import type { Lesson, ResultsDraft } from '../types';
export function useLessonIntegrations(lesson: Lesson, onCommit: (lesson: Lesson) => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [approval, setApproval] = useState<CalendarApproval | null>(null);
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
  return {
    busy,
    error,
    notice,
    approval,
    generate: () =>
      run(async () => {
        const results = await integrationApi.generateResults(
          lesson.id,
          lesson.duration_minutes || 60,
        );
        onCommit({ ...lesson, materials: { ...lesson.materials, results } });
        setNotice('Черновик готов. Проверьте результаты, ДЗ и следующий план.');
      }),
    accept: (draft: ResultsDraft) =>
      run(async () => {
        onCommit(await integrationApi.acceptResults(lesson.id, draft));
        setNotice(
          'Результаты приняты. Сообщение будет отправлено, если включён Telegram и работает worker.',
        );
      }),
    preview: () =>
      run(async () => {
        setApproval(await integrationApi.previewHomework(lesson.id));
      }),
    cancel: () =>
      run(async () => {
        if (approval) await integrationApi.cancelApproval(approval.id);
        setApproval(null);
      }),
    confirm: () =>
      run(async () => {
        if (!approval) return;
        await integrationApi.confirmHomework(approval.id);
        setApproval(null);
        setNotice('Домашнее задание добавлено в описание события.');
      }),
  };
}
