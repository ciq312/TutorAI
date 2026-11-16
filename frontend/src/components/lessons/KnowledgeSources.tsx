import type { KnowledgeSource } from '../../types';
export function KnowledgeSources({ sources }: { sources?: KnowledgeSource[] }) {
  if (!sources?.length) return null;
  return (
    <details className="my-4">
      <summary>Материалы библиотеки · {sources.length}</summary>
      {sources.map((s, i) => (
        <div key={`${s.document_id}-${s.page}-${i}`} className="my-4 text-xs text-muted">
          <a
            className="text-accent underline"
            href={`/api/knowledge/documents/${s.document_id}/file#page=${s.page}`}
            target="_blank"
            rel="noreferrer"
          >
            [К{i + 1}] {s.title} · стр. {s.page}
          </a>
          <p className="whitespace-pre-wrap">{s.text}</p>
        </div>
      ))}
    </details>
  );
}
