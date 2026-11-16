import { useEffect, useId, useRef } from 'react';
import { LoaderCircle, Trash2 } from 'lucide-react';
import type { Student } from '../../types';
import { useDeleteStudent } from '../../hooks/useDeleteStudent';
import { ui } from '../ui/styles';
type Props = {
  student: Student;
  open: boolean;
  onClose: () => void;
  onDeleted: (id: string) => void;
};
export function DeleteStudentDialog({ student, open, onClose, onDeleted }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const title = useId();
  const description = useId();
  const { busy, error, remove } = useDeleteStudent(student.id, onDeleted);
  useEffect(() => {
    if (open) ref.current?.showModal();
    else ref.current?.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-labelledby={title}
      aria-describedby={description}
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else onClose();
      }}
      onClose={onClose}
      className="fixed inset-0 m-auto w-[calc(100%-32px)] max-w-[440px] rounded-2xl border border-[#62424f] bg-surface p-6 text-[#eee8fa] backdrop:bg-[#0e0c17ba] backdrop:backdrop-blur-[5px]"
    >
      <span className="mb-4 grid size-10 place-items-center rounded-xl bg-[#4b2f3b] text-[#f3aabe]">
        <Trash2 size={20} />
      </span>
      <h2 id={title}>Удалить ученика?</h2>
      <p id={description} className="text-[12px] text-muted">
        Профиль <strong className="text-[#e3d6e5]">{student.name}</strong>, все его занятия,
        материалы и контакты будут удалены без возможности восстановления.
      </p>
      {error && (
        <p role="alert" className={ui.error}>
          {error}
        </p>
      )}
      <div className="mt-6 flex justify-end gap-3">
        <button autoFocus type="button" disabled={busy} onClick={onClose} className={ui.secondary}>
          Отмена
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => void remove()}
          className="flex items-center justify-center gap-2 rounded-lg bg-[#b34763] px-4 py-3 text-[11px] font-bold text-white hover:bg-[#c6516f] disabled:opacity-50"
        >
          {busy ? (
            <LoaderCircle size={14} className="motion-safe:animate-spin" />
          ) : (
            <Trash2 size={14} />
          )}
          Удалить
        </button>
      </div>
    </dialog>
  );
}
