import { DeleteStudentDialog } from '../components/students/DeleteStudentDialog';
import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { useStudentProfile } from '../hooks/useStudentProfile';
import { StudentProfileForm } from '../components/students/StudentProfileForm';
import { ui } from '../components/ui/styles';
import { LessonCard } from '../components/lessons/LessonCard';
import { ArrowLeft, BookOpen, GraduationCap, Plus, Sparkles } from 'lucide-react';
import type { Workspace } from '../hooks/useWorkspace';
import { initials } from '../utils/format';

type Props = Pick<
  Workspace,
  | 'selected'
  | 'setPage'
  | 'setModal'
  | 'loading'
  | 'lessons'
  | 'commitStudent'
  | 'openLesson'
  | 'removeStudent'
  | 'removeStudent'
>;
export function StudentPage({
  selected,
  setPage,
  setModal,
  loading,
  lessons,
  commitStudent,
  openLesson,
  removeStudent,
}: Props) {
  const [deleting, setDeleting] = useState(false);
  const profile = useStudentProfile(selected, commitStudent);
  if (!selected) return null;
  return (
    <>
      <button className={ui['back']} onClick={() => setPage('students')}>
        <ArrowLeft size={16} />
        Все ученики
      </button>
      <div className={ui['page-heading']}>
        <div className="flex gap-[18px] items-center [&_h1]:text-[25px] max-[760px]:[&_h1]:text-[22px]">
          <span className="w-[51px] h-[51px] inline-flex items-center justify-center shrink-0 rounded-[17px] bg-[#453b5e] text-[#d5c4ff] font-[750] text-[17px] max-[760px]:w-[43px] max-[760px]:h-[43px] max-[760px]:text-[14px] max-[760px]:rounded-[13px]">
            {initials(selected.name)}
          </span>
          <div>
            <h1>{selected.name}</h1>
            <p>{selected.grade || 'Класс не указан'}</p>
          </div>
        </div>
        <button
          className={ui['primary']}
          onClick={() => {
            const next = lessons
              .filter((l) => l.status !== 'cancelled' && new Date(l.scheduled_at) > new Date())
              .sort(
                (a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime(),
              )[0];
            if (next) openLesson(next);
            else setModal('lesson');
          }}
        >
          <Sparkles size={17} />
          Подготовить урок
        </button>
      </div>
      <div className="grid [grid-template-columns:minmax(0,1fr)_280px] gap-[22px] items-start max-[1150px]:[grid-template-columns:minmax(0,1fr)]">
        <section className={ui['panel']}>
          <div className={ui['section-toolbar']}>
            <h2>История занятий</h2>
            <button className={ui['secondary']} onClick={() => setModal('lesson')}>
              <Plus size={16} />
              Занятие
            </button>
          </div>
          {loading ? (
            <p>Загружаем историю…</p>
          ) : !lessons.length ? (
            <div className={ui['empty']}>
              <BookOpen />
              <h3>Здесь начинается история</h3>
              <p>Добавьте занятие и заметки, чтобы AI мог учитывать контекст.</p>
              <button className={ui['primary']} onClick={() => setModal('lesson')}>
                Добавить занятие
              </button>
            </div>
          ) : (
            lessons.map((l) => <LessonCard key={l.id} lesson={l} onOpen={openLesson} />)
          )}
        </section>
        <aside className="bg-surface border border-line rounded-[14px] p-[25px] min-w-0 max-[760px]:p-[20px] text-[11px] text-[#a8a6bc] wrap-anywhere [&_h3]:text-[13px] [&_h3]:text-[#ddd9ed] [&_h3]:flex [&_h3]:gap-[9px] [&_h3]:items-center [&_hr]:border-0 [&_hr]:border-t border-line [&_hr]:m-[23px_0] max-[1150px]:order-[2]">
          <span className="grid place-items-center w-[33px] h-[33px] bg-[#494061] text-[#c8baff] rounded-[10px]">
            <GraduationCap size={21} />
          </span>
          <h3>Цель обучения</h3>
          <p>{selected.goals || 'Цель пока не указана'}</p>
          <hr />
          <StudentProfileForm student={selected} {...profile} onSave={profile.save} />
          <div className="mt-5 border-t border-line pt-4">
            <button
              className="flex items-center gap-2 text-[11px] text-[#ecaabd]"
              disabled={profile.busy}
              onClick={() => setDeleting(true)}
            >
              <Trash2 size={14} />
              Удалить ученика
            </button>
          </div>
          <h3>Контекст имеет значение</h3>
          <p>
            В план попадут последние занятия и связанные с темой заметки из истории этого ученика.
          </p>
        </aside>
      </div>
      <DeleteStudentDialog
        key={selected.id}
        student={selected}
        open={deleting}
        onClose={() => setDeleting(false)}
        onDeleted={removeStudent}
      />
    </>
  );
}
