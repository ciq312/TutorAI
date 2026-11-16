import { useRef, useState } from 'react';
import { tutorApi } from '../services/tutorApi';
export function useDeleteStudent(id: string, onDeleted: (id: string) => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const running = useRef(false);
  async function remove() {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError('');
    try {
      await tutorApi.deleteStudent(id);
      onDeleted(id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      running.current = false;
      setBusy(false);
    }
  }
  return { busy, error, remove };
}
