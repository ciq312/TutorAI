import { useState, type FormEvent } from 'react';
import { tutorApi } from '../services/tutorApi';
import type { Student } from '../types';
export function useStudentProfile(student: Student | null, onCommit: (student: Student) => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!student) return;
    const data = new FormData(e.currentTarget);
    setBusy(true);
    setSaved(false);
    setError('');
    try {
      const body = {
        name: String(data.get('name')).trim(),
        grade: String(data.get('grade')).trim() || null,
        goals: String(data.get('goals')).trim() || null,
      };
      onCommit(await tutorApi.updateStudent(student.id, body));
      setSaved(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, saved, save };
}
