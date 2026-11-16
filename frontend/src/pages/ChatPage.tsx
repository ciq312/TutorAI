import { StudentPicker } from '../components/layout/StudentPicker';
import { useEffect, useRef } from 'react';
import { BookOpen, CalendarDays, MessageSquarePlus, Sparkles } from 'lucide-react';
import { useChat } from '../hooks/useChat';
import { ChatComposer } from '../components/chat/ChatComposer';
import { ChatBubble } from '../components/chat/ChatBubble';
import type { ChatMessage, Student } from '../types';

type Props = {
  selected: Student | null;
  students: Student[];
  loading: boolean;
  onSelect: (student: Student | null) => void;
  onHistory: () => void;
  onCalendar: () => void;
};
export function ChatPage({ selected, students, loading, onSelect, onHistory, onCalendar }: Props) {
  const { messages, pending, error, send, clear } = useChat(selected);
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (messages.length) bottom.current?.scrollIntoView({ block: 'nearest' });
  }, [messages, pending]);
  return (
    <div className="mx-auto flex min-h-[calc(100dvh-200px)] max-w-[850px] flex-col">
      <div className="mb-7 flex justify-center">
        <StudentPicker
          students={students}
          selected={selected}
          loading={loading}
          onSelect={onSelect}
        />
      </div>
      <div className="mb-6 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-[11px] text-muted">
          <span className="size-1.5 rounded-full bg-[#8dcab5]" />
          Ассистент репетитора
        </div>
        <div className="flex gap-4">
          <button
            onClick={onHistory}
            disabled={!selected}
            className="flex items-center gap-2 text-[11px] text-muted hover:text-accent"
          >
            <BookOpen size={14} />
            История занятий
          </button>
          <button
            onClick={clear}
            disabled={pending || !messages.length}
            aria-label="Очистить диалог"
            className="text-muted hover:text-accent"
          >
            <MessageSquarePlus size={17} />
          </button>
        </div>
      </div>
      {!messages.length ? (
        <div className="flex flex-1 flex-col items-center justify-center pb-12 text-center">
          <span className="mb-7 grid size-16 place-items-center rounded-[22px] border border-[#64517d] bg-gradient-to-br from-[#665183] to-[#30273f] text-[#d9c6ff] shadow-[0_0_65px_#9571d41a]">
            <Sparkles size={29} strokeWidth={1.4} />
          </span>
          <div className="mb-3 text-[9px] font-bold tracking-[2px] text-accent">
            ВАШ ОПЫТ + ВОЗМОЖНОСТИ AI
          </div>
          <h1 className="max-w-[600px] text-[30px] leading-snug max-[760px]:text-[24px]">
            Что подготовим на этот раз?
          </h1>
          <p className="max-w-[450px] text-[12px] text-muted">
            {selected
              ? 'Обсудим трудности, соберём план и найдём подходящие упражнения — с учётом истории ученика.'
              : 'Выберите ученика сверху. Нового ученика можно добавить во вкладке «Ученики».'}
          </p>
          <div className="mt-8 grid w-full max-w-[620px] grid-cols-2 gap-3 max-[500px]:grid-cols-1">
            {[
              'Помоги составить план следующего занятия',
              'Какие трудности стоит повторить?',
              'Предложи упражнения для закрепления',
            ].map((prompt) => (
              <button
                key={prompt}
                disabled={!selected || pending}
                onClick={() => void send(prompt)}
                className="rounded-xl border border-line bg-surface p-4 text-left text-[11px] leading-6 text-[#c6bfd5] hover:border-[#7c659c]"
              >
                {prompt} <span className="text-accent">↗</span>
              </button>
            ))}
            <button
              onClick={onCalendar}
              className="flex items-center gap-3 rounded-xl border border-line bg-surface p-4 text-left text-[11px] text-[#c6bfd5]"
            >
              <CalendarDays size={18} className="text-accent" />
              Открыть календарь занятий
            </button>
          </div>
        </div>
      ) : (
        <div
          role="log"
          aria-label="Диалог с ассистентом"
          aria-live="polite"
          className="flex-1 space-y-6 pb-8"
        >
          {messages.map((message: ChatMessage) => (
            <ChatBubble key={message.id} message={message} />
          ))}
          {pending && (
            <div role="status" className="flex items-center gap-3 text-[12px] text-muted">
              <Sparkles size={17} className="text-accent" />
              Изучаю контекст и готовлю ответ…
            </div>
          )}
          <div ref={bottom} />
        </div>
      )}
      <div className="sticky bottom-0 mt-auto bg-canvas pb-3 pt-3">
        {error && (
          <p role="alert" className="rounded-xl bg-[#49313b] p-3 text-[12px] text-[#ffd2df]">
            {error} Можно повторно отправить вопрос.
          </p>
        )}
        <ChatComposer key={selected?.id} disabled={!selected} pending={pending} onSend={send} />
        <p className="mb-0 text-center text-[9px] text-muted">
          AI может ошибаться. Проверяйте факты и задания. Диалог хранится только в этой сессии.
        </p>
      </div>
    </div>
  );
}
