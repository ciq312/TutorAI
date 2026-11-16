import { KnowledgeSources } from '../lessons/KnowledgeSources';
import { Copy, Sparkles, UserRound } from 'lucide-react';
import { useState } from 'react';
import type { ChatMessage } from '../../types';
import { formatDate } from '../../utils/format';
export function ChatBubble({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false);
  const assistant = message.role === 'assistant';
  return (
    <article className={`flex gap-3 ${assistant ? '' : 'flex-row-reverse'}`}>
      <span
        className={`grid size-8 shrink-0 place-items-center rounded-xl ${assistant ? 'bg-[#3e3356] text-accent' : 'bg-[#343643] text-[#cfccdc]'}`}
      >
        {assistant ? <Sparkles size={16} /> : <UserRound size={16} />}
      </span>
      <div
        className={`min-w-0 max-w-[90%] rounded-2xl px-5 py-4 ${assistant ? 'bg-surface' : 'border border-[#514461] bg-[#30283f]'}`}
      >
        <div className="mb-2 text-[10px] font-bold text-muted">
          {assistant ? 'My Tutor AI' : 'Вы'}
        </div>
        <div className="whitespace-pre-wrap wrap-anywhere text-[13px] leading-8">
          {message.content}
        </div>
        {!!message.sources?.length && (
          <details className="mt-4">
            <summary>Источники · {message.sources.length}</summary>
            {message.sources.map((source, i) => (
              <div key={source.lesson_id} className="mt-3 text-[11px] text-muted">
                <strong className="text-accent">
                  [{i + 1}] {formatDate(source.scheduled_at)}
                </strong>
                {source.excerpts.map((text, j) => (
                  <p key={j} className="whitespace-pre-wrap">
                    {text}
                  </p>
                ))}
              </div>
            ))}
          </details>
        )}
        <KnowledgeSources sources={message.knowledge_sources} />
        {assistant && (
          <button
            className="mt-3 flex items-center gap-2 text-[10px] text-muted hover:text-accent"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(message.content);
                setCopied(true);
              } catch {
                setCopied(false);
              }
            }}
          >
            <Copy size={12} />
            {copied ? 'Скопировано' : 'Копировать'}
          </button>
        )}
      </div>
    </article>
  );
}
