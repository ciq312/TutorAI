import { useState, type FormEvent } from 'react';
import { ArrowUp, LoaderCircle } from 'lucide-react';
type Props = { disabled: boolean; pending: boolean; onSend: (message: string) => Promise<void> };
export function ChatComposer({ disabled, pending, onSend }: Props) {
  const [draft, setDraft] = useState('');
  function submit(e: FormEvent) {
    e.preventDefault();
    if (disabled || pending || !draft.trim()) return;
    void onSend(draft);
    setDraft('');
  }
  return (
    <form
      onSubmit={submit}
      className="rounded-2xl border border-[#514663] bg-[#252531] p-3 shadow-[0_12px_50px_#0002] focus-within:border-accent"
    >
      <textarea
        aria-label="Сообщение ассистенту"
        placeholder={
          disabled ? 'Выберите или создайте ученика…' : 'Что подготовим для следующего занятия?'
        }
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        maxLength={4000}
        disabled={disabled || pending}
        rows={2}
        className="m-0 min-h-[70px] resize-none border-0 bg-transparent p-2 text-[14px] focus:shadow-none"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            e.currentTarget.form?.requestSubmit();
          }
        }}
      />
      <div className="flex items-center justify-between px-2">
        <span className="text-[10px] text-muted">
          Enter — отправить · Shift + Enter — новая строка
        </span>
        <button
          type="submit"
          disabled={disabled || pending || !draft.trim()}
          aria-label="Отправить сообщение"
          className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground hover:bg-primary-hover disabled:cursor-not-allowed"
        >
          {pending ? (
            <LoaderCircle size={18} className="motion-safe:animate-spin" />
          ) : (
            <ArrowUp size={20} />
          )}
        </button>
      </div>
    </form>
  );
}
