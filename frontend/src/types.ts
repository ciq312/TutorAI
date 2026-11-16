export type Student = { id: string; name: string; grade: string | null; goals: string | null };
export type Lesson = {
  id: string;
  status?: 'scheduled' | 'completed' | 'cancelled';
  duration_minutes?: number;
  preparation_minutes?: number;
  notifications_enabled?: boolean;
  homework_status?: 'unknown' | 'done' | 'partial' | 'not_done';
  materials?: LessonMaterials;
  student_id: string;
  topic: string;
  scheduled_at: string;
  notes: string | null;
  difficulties: string | null;
  homework: string | null;
};
export type Material = {
  knowledge_sources?: KnowledgeSource[];
  brief?: string;
  plan?: string;
  homework?: string;
  teacher_answers?: string;
  feedback?: string;
  facts: { text: string; source_numbers: number[] }[];
  missing_data: string[];
  warnings: string[];
  sources: { lesson_id: string; scheduled_at: string; excerpts: string[] }[];
};

export type Page =
  'chat' | 'calendar' | 'lesson' | 'students' | 'student' | 'settings' | 'knowledge';
export type MaterialKind = 'plan' | 'homework' | 'feedback';

export type ChatReply = {
  knowledge_sources?: KnowledgeSource[];
  answer: string;
  sources: Material['sources'];
  warnings: string[];
};
export type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Material['sources'];
  knowledge_sources?: KnowledgeSource[];
};

export type LessonDraft = {
  knowledge_sources?: KnowledgeSource[];
  missing_data?: string[];
  warnings?: string[];
  text: string;
  brief: string;
  answers: string;
  sources: Material['sources'];
};
export type LessonMaterials = {
  results?: ResultsDraft | null;
  plan?: LessonDraft | null;
  homework?: LessonDraft | null;
  feedback?: LessonDraft | null;
  next_plan?: LessonDraft | null;
  next_topic?: string | null;
};

export type KnowledgeSource = {
  document_id: string;
  title: string;
  page: number;
  text: string;
  distance: number;
};
export type ResultsDraft = {
  version: string;
  approved: boolean;
  based_on: string;
  summary: string;
  homework: string;
  teacher_answers: string;
  next_topic: string;
  next_plan: string;
  brief: string;
  missing_data: string[];
  warnings: string[];
  sources: Material['sources'];
  knowledge_sources: KnowledgeSource[];
};
