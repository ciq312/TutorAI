import { weeklyDates } from '../utils/calendar';
import { useCallback, useEffect, useState, useRef, type FormEvent } from 'react';
import { tutorApi } from '../services/tutorApi';
import type { Student, Lesson, Page } from '../types';

export function useWorkspace() {
  const initialLesson = useRef(new URLSearchParams(window.location.search).get('lesson'));
  const [page, setPage] = useState<Page>('calendar');
  const [students, setStudents] = useState<Student[]>([]);
  const [selected, setSelected] = useState<Student | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [modal, setModalState] = useState<'student' | 'lesson' | null>(null);
  const [lessonTab, setLessonTab] = useState<import('./useLessonWorkspace').LessonTab>('plan');
  const [openedLesson, setOpenedLesson] = useState<Lesson | null>(null);
  const [lessonDate, setLessonDate] = useState('');
  function setModal(value: 'student' | 'lesson' | null) {
    setModalState(value);
    if (value === null) {
      setLessonDate('');
      setNextLessonSource(null);
    }
  }
  const [recordBusy, setRecordBusy] = useState(false);
  const [calendarRevision, setCalendarRevision] = useState(0);

  useEffect(() => {
    let active = true;
    setError('');
    setStudents([]);
    setSelected(null);
    setLessons([]);
    setOpenedLesson(null);
    setPage('calendar');
    setLoading(true);
    tutorApi
      .listStudents()
      .then((data) => {
        if (active) {
          setStudents(data);
          setSelected(data[0] || null);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setLessons([]);
    if (!selected) {
      setLoading(false);
      return;
    }
    setLoading(true);
    tutorApi
      .listLessons(selected.id)
      .then((data) => {
        if (active) setLessons(data);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selected]);

  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(''), 4000);
    return () => clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    const id = initialLesson.current;
    if (!id || !students.length) return;
    initialLesson.current = null;
    void tutorApi
      .getLesson(id)
      .then((lesson) => {
        setSelected(students.find((s) => s.id === lesson.student_id) || null);
        setOpenedLesson(lesson);
        setPage('lesson');
        const url = new URL(window.location.href);
        url.searchParams.delete('lesson');
        window.history.replaceState(null, '', url);
      })
      .catch((e) => setError(e.message));
  }, [students]);

  const selectStudent = useCallback((student: Student | null) => {
    setSelected(student);
    setError('');
    setPage((current) => (['student', 'students', 'lesson'].includes(current) ? 'chat' : current));
  }, []);
  function openStudent(student: Student) {
    selectStudent(student);
    setPage('student');
  }

  const [nextLessonSource, setNextLessonSource] = useState<Lesson | null>(null);
  function scheduleNext(lesson: Lesson) {
    const date = new Date(lesson.scheduled_at);
    date.setDate(date.getDate() + 7);
    setLessonDate(
      new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16),
    );
    setNextLessonSource(lesson);
    setModal('lesson');
  }
  function openLesson(lesson: Lesson, tab: import('./useLessonWorkspace').LessonTab = 'plan') {
    setLessonTab(tab);
    setSelected(students.find((student) => student.id === lesson.student_id) ?? null);
    setOpenedLesson(lesson);
    setPage('lesson');
    setError('');
  }
  function commitLesson(lesson: Lesson) {
    setOpenedLesson((current) => (current?.id === lesson.id ? lesson : current));
    setLessons((old) => old.map((current) => (current.id === lesson.id ? lesson : current)));
    setCalendarRevision((old) => old + 1);
  }
  function importCalendarLesson(student: Student, lesson: Lesson) {
    setStudents((old) => (old.some((s) => s.id === student.id) ? old : [...old, student]));
    setCalendarRevision((old) => old + 1);
    if (selected?.id === lesson.student_id) {
      setLessons((old) => (old.some((l) => l.id === lesson.id) ? old : [...old, lesson]));
    }
    setNotice('Ученик привязан к событию календаря');
  }
  function commitStudent(student: Student) {
    setStudents((old) => old.map((current) => (current.id === student.id ? student : current)));
    setSelected((current) => (current?.id === student.id ? student : current));
  }
  function removeStudent(id: string) {
    setStudents((old) => old.filter((student) => student.id !== id));
    setSelected((current) => (current?.id === id ? null : current));
    setOpenedLesson((current) => (current?.student_id === id ? null : current));
    setNextLessonSource((current) => (current?.student_id === id ? null : current));
    setLessons((old) => old.filter((lesson) => lesson.student_id !== id));
    setCalendarRevision((old) => old + 1);
    setPage('students');
    setError('');
    setNotice('Ученик удалён');
  }
  async function saveForm(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setRecordBusy(true);
    setError('');
    try {
      if (modal === 'student') {
        const body = {
          name: String(data.get('name')).trim(),
          grade: String(data.get('grade')).trim() || null,
          goals: String(data.get('goals')).trim() || null,
        };
        const student = await tutorApi.createStudent(body);
        setStudents((old) => [...old, student]);
        selectStudent(student);
        setNotice('Ученик добавлен');
      } else if (selected) {
        const body = {
          topic: String(data.get('topic')).trim() || 'Тема уточняется',
          duration_minutes: Number(data.get('duration_minutes') || 60),
          preparation_minutes: Number(data.get('preparation_minutes') || 30),
          status: 'scheduled' as const,
          scheduled_at: new Date(String(data.get('scheduled_at'))).toISOString(),
          notes: String(data.get('notes')).trim() || null,
          difficulties: String(data.get('difficulties')).trim() || null,
          homework: null,
          materials:
            nextLessonSource?.student_id === selected.id && nextLessonSource?.materials?.next_plan
              ? { plan: nextLessonSource.materials.next_plan }
              : {},
        };
        const dates = weeklyDates(body.scheduled_at, Number(data.get('repeat_count') || 1));
        const created: Lesson[] = [];
        let creationError = '';
        for (const [index, scheduled_at] of dates.entries()) {
          try {
            const input = { ...body, scheduled_at, materials: index === 0 ? body.materials : {} };
            created.push(await tutorApi.createLesson(selected.id, input));
          } catch (e) {
            if (!created.length) throw e;
            creationError = `Создано ${created.length} из ${dates.length} занятий. ${(e as Error).message}`;
            break;
          }
        }
        const lesson = created[0];
        setLessons((old) => [...created, ...old]);
        if (creationError) setError(creationError);
        setCalendarRevision((old) => old + 1);
        setOpenedLesson(lesson);
        setLessonTab('plan');
        setPage('lesson');
        setNotice(`Сохранено занятий: ${created.length}`);
      }
      setModal(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRecordBusy(false);
    }
  }
  return {
    importCalendarLesson,
    page,
    setPage,
    openedLesson,
    lessonTab,
    nextLessonSource,
    scheduleNext,
    openLesson,
    commitLesson,
    commitStudent,
    removeStudent,
    students,
    selected,
    lessons,
    query,
    setQuery,
    loading,
    error,
    setError,
    notice,
    setNotice,
    modal,
    setModal,
    recordBusy,
    lessonDate,
    setLessonDate,
    selectStudent,
    openStudent,
    saveForm,
    calendarRevision,
  };
}
export type Workspace = ReturnType<typeof useWorkspace>;
