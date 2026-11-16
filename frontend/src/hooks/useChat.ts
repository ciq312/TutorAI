import { useEffect, useRef, useState } from 'react';
import { tutorApi } from '../services/tutorApi';
import type { ChatMessage, ChatReply, Student } from '../types';

type Conversation = { messages: ChatMessage[]; pending: boolean; error: string };
const empty: Conversation = { messages: [], pending: false, error: '' };
export function useChat(student: Student | null) {
  const [conversations, setConversations] = useState<Record<string, Conversation>>({});
  const pending = useRef(new Set<string>());
  const generation = useRef(0);
  useEffect(() => {
    generation.current += 1;
    pending.current.clear();
    setConversations({});
  }, []);
  const key = student?.id ?? '';
  const conversation = conversations[key] ?? empty;
  async function send(text: string) {
    const content = text.trim();
    if (!student || !content || pending.current.has(key)) return;
    const version = generation.current;
    pending.current.add(key);
    const history = conversation.messages;
    const message: ChatMessage = { id: crypto.randomUUID(), role: 'user', content };
    setConversations((old) => ({
      ...old,
      [key]: { messages: [...history, message], pending: true, error: '' },
    }));
    try {
      const reply: ChatReply = await tutorApi.chat(student.id, content, history);
      if (generation.current !== version) return;
      setConversations((old) => ({
        ...old,
        [key]: {
          messages: [
            ...old[key].messages,
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: reply.answer,
              sources: reply.sources,
              knowledge_sources: reply.knowledge_sources,
            },
          ],
          pending: false,
          error: '',
        },
      }));
    } catch (e) {
      if (generation.current === version)
        setConversations((old) => ({
          ...old,
          [key]: { ...old[key], pending: false, error: (e as Error).message },
        }));
    } finally {
      if (generation.current === version) pending.current.delete(key);
    }
  }
  function clear() {
    if (!pending.current.has(key)) setConversations((old) => ({ ...old, [key]: empty }));
  }
  return { ...conversation, send, clear };
}
