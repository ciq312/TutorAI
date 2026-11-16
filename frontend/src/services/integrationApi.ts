import { api } from '../api';
import type { Lesson, Student, KnowledgeSource, ResultsDraft } from '../types';

export type NotificationSettings = {
  brief_enabled: boolean;
  results_enabled: boolean;
  reminder_enabled: boolean;
  before_minutes: number;
  after_minutes: number;
  timezone: string;
};
export type CalendarSelection = { calendar_id: string; mode: 'mixed' | 'teaching' };
export type IntegrationStatus = {
  google_configured: boolean;
  google_connected: boolean;
  calendars: CalendarSelection[];
  last_sync: string | null;
  sync_error: string | null;
  telegram_configured: boolean;
  telegram_connected: boolean;
  notifications: NotificationSettings;
  worker_heartbeat: string | null;
  worker_error: string | null;
};
export type GoogleCalendar = { id: string; summary: string; access_role: string };
export type CalendarEvent = {
  id: string;
  calendar_id: string;
  external_id: string;
  series_id: string | null;
  title: string;
  starts_at: string | null;
  ends_at: string | null;
  status: string;
  decision: string;
  lesson_id: string | null;
  suggested_students: { id: string; name: string }[];
  calendar_mode: string;
};
export type CalendarApproval = {
  id: string;
  event_id: string;
  homework: string;
  description: string;
  status: string;
  expires_at: string;
  event_title: string;
  starts_at: string | null;
  visibility_notice: string;
};
export type CurriculumTopic = { title: string; objectives: string; page: number };
export type KnowledgeDocument = {
  id: string;
  title: string;
  filename: string;
  kind: string;
  status: string;
  error: string | null;
  topics: CurriculumTopic[];
};
export type Curriculum = {
  document_id: string;
  title: string;
  topic_index: number;
  current_topic: CurriculumTopic;
  following_topics: CurriculumTopic[];
};
export type Delivery = {
  student_name: string;
  scheduled_at: string;
  kind: string;
  key: string;
  lesson_id: string;
  status: string;
  attempts: number;
  error: string | null;
};

async function all<T>(path: string): Promise<T[]> {
  const result: T[] = [];
  for (let offset = 0; ; offset += 100) {
    const batch = await api<T[]>(
      `${path}${path.includes('?') ? '&' : '?'}limit=100&offset=${offset}`,
    );
    result.push(...batch);
    if (batch.length < 100) return result;
  }
}
export const integrationApi = {
  status: () => api<IntegrationStatus>('/integrations/status'),
  connectGoogle: () => api<{ url: string }>('/integrations/google/connect', 'POST'),
  disconnectGoogle: () => api('/integrations/google', 'DELETE'),
  calendars: () => api<GoogleCalendar[]>('/integrations/google/calendars'),
  selectCalendars: (calendars: CalendarSelection[]) =>
    api('/integrations/google/calendars', 'PUT', { calendars }),
  sync: () => api('/integrations/google/sync', 'POST'),
  events: () => all<CalendarEvent>('/integrations/google/events'),
  decide: (
    id: string,
    body: {
      action: 'link' | 'ignore';
      student_id?: string;
      new_student?: { name: string };
      whole_series?: boolean;
    },
  ) =>
    api<{ lesson: Lesson | null; student: Student | null }>(
      `/integrations/google/events/${id}/decision`,
      'POST',
      body,
    ),
  connectTelegram: () => api<{ url: string }>('/integrations/telegram/connect', 'POST'),
  checkTelegram: () => api<{ connected: boolean }>('/integrations/telegram/check', 'POST'),
  disconnectTelegram: () => api('/integrations/telegram', 'DELETE'),
  notifications: (settings: NotificationSettings) =>
    api('/integrations/notifications', 'PUT', settings),
  previewHomework: (id: string) =>
    api<CalendarApproval>(`/integrations/lessons/${id}/calendar-homework/preview`, 'POST'),
  confirmHomework: (id: string) =>
    api<CalendarApproval>(`/integrations/calendar-approvals/${id}/confirm`, 'POST'),
  cancelApproval: (id: string) => api(`/integrations/calendar-approvals/${id}`, 'DELETE'),
  deliveries: () => api<Delivery[]>('/integrations/notifications/deliveries'),
  retryDelivery: (key: string) => api('/integrations/notifications/retry', 'POST', { key }),
  documents: () => all<KnowledgeDocument>('/knowledge/documents'),
  async upload(file: File, title: string, kind: string): Promise<KnowledgeDocument> {
    const body = new FormData();
    body.set('file', file);
    body.set('title', title);
    body.set('kind', kind);
    const response = await fetch('/api/knowledge/documents', { method: 'POST', body });
    if (!response.ok)
      throw new Error(
        response.status === 413
          ? 'Максимальный размер файла — 15 МБ.'
          : 'Не удалось загрузить документ. Нужен PDF или TXT в UTF-8.',
      );
    return response.json();
  },
  deleteDocument: (id: string) => api(`/knowledge/documents/${id}`, 'DELETE'),
  reindex: (id: string) => api(`/knowledge/documents/${id}/reindex`, 'POST'),
  search: (query: string) => api<KnowledgeSource[]>('/knowledge/search', 'POST', { query }),
  extractTopics: (id: string) =>
    api<{ topics: CurriculumTopic[]; truncated: boolean }>(
      `/knowledge/documents/${id}/topics/draft`,
      'POST',
    ),
  saveTopics: (id: string, topics: CurriculumTopic[]) =>
    api(`/knowledge/documents/${id}/topics`, 'PUT', { topics }),
  curriculum: (studentId: string) => api<Curriculum | null>(`/students/${studentId}/curriculum`),
  assign: (studentId: string, documentId: string, topicIndex: number) =>
    api(`/students/${studentId}/curriculum`, 'PUT', {
      document_id: documentId,
      topic_index: topicIndex,
    }),
  unassign: (studentId: string) => api(`/students/${studentId}/curriculum`, 'DELETE'),
  generateResults: (id: string, duration: number) =>
    api<ResultsDraft>(`/lessons/${id}/results/draft`, 'POST', { duration_minutes: duration }),
  acceptResults: (id: string, draft: ResultsDraft) =>
    api<Lesson>(
      `/lessons/${id}/results`,
      'PUT',
      Object.fromEntries(
        [
          'version',
          'summary',
          'homework',
          'teacher_answers',
          'next_topic',
          'next_plan',
          'brief',
        ].map((k) => [k, draft[k as keyof ResultsDraft]]),
      ),
    ),
};
