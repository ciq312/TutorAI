import { useEffect, useState } from 'react';
import { tutorApi } from '../services/tutorApi';
import type { Student, Lesson } from '../types';
export function useCalendar(students: Student[], enabled: boolean, revision: number) {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    setLoading(true);
    setError('');
    setLessons([]);
    function load() {
      Promise.allSettled(students.map((student) => tutorApi.listLessons(student.id)))
        .then((results) => {
          if (!active) return;
          const failed = results.filter((r) => r.status === 'rejected').length;
          setLessons(results.flatMap((r) => (r.status === 'fulfilled' ? r.value : [])));
          setError('');
          if (failed)
            setError(
              `Не удалось загрузить занятия ${failed} учеников. Календарь показан не полностью.`,
            );
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }
    load();
    const timer = window.setInterval(load, 30000);
    return () => {
      window.clearInterval(timer);
      active = false;
    };
  }, [students, enabled, revision]);
  return { lessons, loading, error };
}
