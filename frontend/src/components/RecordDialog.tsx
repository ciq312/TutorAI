import { DateTimePicker } from './ui/DateTimePicker';
import { ui } from './ui/styles';
import { useEffect, useRef } from 'react';
import { LoaderCircle, Plus, X } from 'lucide-react';
import type { Workspace } from '../hooks/useWorkspace';
type Props = Pick<
  Workspace,
  | 'modal'
  | 'recordBusy'
  | 'setModal'
  | 'saveForm'
  | 'error'
  | 'lessonDate'
  | 'selected'
  | 'students'
  | 'selectStudent'
  | 'nextLessonSource'
> & { defaultPreparationMinutes: number };
export function RecordDialog({
  modal,
  recordBusy: busy,
  setModal,
  saveForm,
  error,
  lessonDate,
  selected,
  students,
  selectStudent,
  nextLessonSource,
  defaultPreparationMinutes,
}: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (modal) dialog.current?.showModal();
    else dialog.current?.close();
  }, [modal]);
  return (
    <dialog
      className="fixed inset-0 m-auto [border:1px_solid_#4f4564] rounded-[16px] bg-surface text-[#eee8fa] max-w-[490px] w-[calc(100%_-_32px)] p-[28px] max-h-[90dvh] overflow-y-auto [&::backdrop]:bg-[#0e0c17ba] [&::backdrop]:backdrop-blur-[5px]"
      ref={dialog}
      onCancel={(event) => {
        if (busy) event.preventDefault();
        if (!busy) setModal(null);
      }}
      onClose={() => setModal(null)}
    >
      <form onSubmit={saveForm}>
        <div className="flex items-center justify-between mb-[25px]">
          <h2>{modal === 'student' ? 'Новый ученик' : 'Новое занятие'}</h2>
          <button
            type="button"
            className={ui['icon-btn']}
            disabled={busy}
            onClick={() => setModal(null)}
            aria-label="Закрыть"
          >
            <X />
          </button>
        </div>
        {modal === 'student' ? (
          <>
            <label>
              Имя и фамилия
              <input name="name" required maxLength={200} autoFocus placeholder="Имя и фамилия" />
            </label>
            <label>
              Класс / уровень
              <input name="grade" maxLength={100} placeholder="8 класс" />
            </label>
            <label>
              Цель обучения
              <textarea name="goals" maxLength={20000} placeholder="Чего хочет достичь ученик?" />
            </label>
          </>
        ) : (
          <>
            <label>
              Ученик
              <select
                required
                value={selected?.id ?? ''}
                onChange={(e) =>
                  selectStudent(students.find((s) => s.id === e.target.value) ?? null)
                }
              >
                <option value="">Выберите ученика</option>
                {students.map((student) => (
                  <option value={student.id} key={student.id}>
                    {student.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Тема — можно уточнить позже
              <input
                name="topic"
                maxLength={500}
                defaultValue={nextLessonSource?.materials?.next_topic || ''}
                placeholder="Тема следующего урока"
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label>
                Длительность, мин
                <input
                  name="duration_minutes"
                  type="number"
                  required
                  min={10}
                  max={240}
                  defaultValue={nextLessonSource?.duration_minutes || 60}
                />
              </label>
              <label>
                Подготовить за, мин
                <input
                  name="preparation_minutes"
                  type="number"
                  required
                  min={0}
                  max={10080}
                  defaultValue={nextLessonSource?.preparation_minutes ?? defaultPreparationMinutes}
                />
              </label>
            </div>
            <p className="text-[10px] text-muted">
              Настройка времени сохраняется. Автоматическая подготовка по таймеру ещё не подключена.
            </p>
            <label>
              Дата и время
              <DateTimePicker
                name="scheduled_at"
                required
                defaultValue={
                  lessonDate ||
                  new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
                    .toISOString()
                    .slice(0, 16)
                }
              />
            </label>
            <label>
              Повторение
              <select name="repeat_count" defaultValue="1">
                <option value="1">Одно занятие</option>
                <option value="4">Еженедельно — создать 4 занятия</option>
                <option value="8">Еженедельно — создать 8 занятий</option>
              </select>
            </label>
            <label>
              Что разобрали
              <textarea name="notes" maxLength={20000} />
            </label>
            <label>
              Какие возникли трудности
              <textarea name="difficulties" maxLength={20000} />
            </label>
          </>
        )}
        {error && (
          <p className={ui['error']} role="alert">
            {error}
          </p>
        )}
        <button className={ui['primary']} disabled={busy}>
          {busy ? (
            <LoaderCircle className="motion-safe:animate-spin" size={16} />
          ) : (
            <Plus size={16} />
          )}
          Сохранить
        </button>
      </form>
    </dialog>
  );
}
