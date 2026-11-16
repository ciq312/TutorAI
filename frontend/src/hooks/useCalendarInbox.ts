import { useEffect, useState, useCallback } from 'react';
import { integrationApi, type CalendarEvent } from '../services/integrationApi';
import type { Student, Lesson } from '../types';
export function useCalendarInbox(
  enabled: boolean,
  onImported: (student: Student, lesson: Lesson) => void,
) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    const next = await integrationApi.events();
    setEvents(next);
    setError('');
  }, []);
  useEffect(() => {
    if (!enabled) return;
    const refresh = () => {
      void load().catch((e) => setError(e.message));
    };
    refresh();
    const timer = window.setInterval(refresh, 30000);
    return () => window.clearInterval(timer);
  }, [enabled, load]);
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError('');
    try {
      await action();
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return {
    events,
    busy,
    error,
    refresh: () =>
      run(async () => {
        await integrationApi.sync();
      }),
    decide: (id: string, body: Parameters<typeof integrationApi.decide>[1]) =>
      run(async () => {
        const result = await integrationApi.decide(id, body);
        if (result.student && result.lesson) onImported(result.student, result.lesson);
      }),
  };
}
