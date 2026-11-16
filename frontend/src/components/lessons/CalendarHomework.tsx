import { useEffect, useRef } from 'react';
import type { Lesson } from '../../types';
import { useLessonIntegrations } from '../../hooks/useLessonIntegrations';
import { ui } from '../ui/styles';
export function CalendarHomework({ lesson }: { lesson: Lesson }) {
  const vm = useLessonIntegrations(lesson, () => {});
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (vm.approval) dialog.current?.showModal();
    else dialog.current?.close();
  }, [vm.approval]);
  return (
    <div className="mt-4">
      <button
        className={ui.secondary}
        disabled={vm.busy || !lesson.homework || lesson.status === 'cancelled'}
        onClick={() => void vm.preview()}
      >
        Добавить принятое ДЗ в Google Calendar
      </button>
      <p className="text-xs text-muted">
        Для занятия, привязанного к событию Google. Сначала покажем точный текст изменения.
      </p>
      {vm.error && (
        <p className={ui.error} role="alert">
          {vm.error}
        </p>
      )}
      {vm.notice && (
        <p className="text-accent" role="status">
          {vm.notice}
        </p>
      )}
      <dialog
        ref={dialog}
        onCancel={(e) => {
          e.preventDefault();
          if (!vm.busy) void vm.cancel();
        }}
        className="m-auto max-h-[85dvh] w-[min(90vw,650px)] overflow-auto rounded-2xl border border-line bg-surface p-6 text-foreground backdrop:bg-black/60"
        aria-labelledby="calendar-approval-title"
      >
        <h2 id="calendar-approval-title">Подтвердить изменение события</h2>
        {vm.approval && (
          <>
            <p>
              {vm.approval.event_title} ·{' '}
              {vm.approval.starts_at ? new Date(vm.approval.starts_at).toLocaleString('ru-RU') : ''}
            </p>
            <p className={ui.difficulty}>{vm.approval.visibility_notice}</p>
            <h3>Новое описание события целиком</h3>
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap wrap-anywhere rounded-xl border border-line p-4 text-xs">
              {vm.approval.description}
            </pre>
            <div className="mt-5 flex gap-3">
              <button className={ui.primary} disabled={vm.busy} onClick={() => void vm.confirm()}>
                Подтвердить запись
              </button>
              <button className={ui.secondary} disabled={vm.busy} onClick={() => void vm.cancel()}>
                Отмена
              </button>
            </div>
          </>
        )}
        {vm.error && (
          <p role="alert" className={ui.error}>
            {vm.error}
          </p>
        )}
      </dialog>
    </div>
  );
}
