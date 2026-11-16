import { api } from '../api';
import type { Student, Lesson, Material, ChatReply, ChatMessage } from '../types';

type StudentInput = Omit<Student, 'id'>;
type LessonInput = Omit<Lesson, 'id' | 'student_id'>;
type MaterialRequest =
  | { kind: 'plan'; studentId: string; topic: string; duration: number; instructions?: string }
  | { kind: 'homework'; lessonId: string; duration: number; instructions?: string }
  | { kind: 'feedback'; lessonId: string; recipient: string; instructions?: string };

async function listAll<T>(path: string): Promise<T[]> {
  const result: T[] = [];
  for (let offset = 0; ; offset += 100) {
    const batch = await api<T[]>(`${path}?limit=100&offset=${offset}`);
    result.push(...batch);
    if (batch.length < 100) return result;
  }
}
export const tutorApi = {
  chat: (studentId: string, message: string, history: ChatMessage[]) =>
    api<ChatReply>(`/students/${studentId}/chat`, 'POST', {
      message,
      history: history
        .slice(-12)
        .map(({ role, content }) => ({ role, content: content.slice(0, 4000) })),
    }),
  getLesson: (id: string) => api<Lesson>(`/lessons/${id}`),
  listStudents: () => listAll<Student>('/students'),
  listLessons: (studentId: string) => listAll<Lesson>(`/students/${studentId}/lessons`),
  deleteStudent: (id: string) => api<void>(`/students/${id}`, 'DELETE'),
  createStudent: (body: StudentInput) => api<Student>('/students', 'POST', body),
  createLesson: (studentId: string, body: LessonInput) =>
    api<Lesson>(`/students/${studentId}/lessons`, 'POST', body),
  updateLesson: (id: string, body: Partial<LessonInput>) =>
    api<Lesson>(`/lessons/${id}`, 'PATCH', body),
  updateStudent: (id: string, body: Partial<StudentInput>) =>
    api<Student>(`/students/${id}`, 'PATCH', body),
  saveHomework: (lessonId: string, homework: string) =>
    api<Lesson>(`/lessons/${lessonId}/homework`, 'PUT', { homework }),
  generateMaterial(request: MaterialRequest): Promise<Material> {
    switch (request.kind) {
      case 'plan':
        return api(`/students/${request.studentId}/lesson-plan`, 'POST', {
          topic: request.topic,
          ...(request.instructions ? { instructions: request.instructions } : {}),
          duration_minutes: request.duration,
        });
      case 'homework':
        return api(`/lessons/${request.lessonId}/homework/draft`, 'POST', {
          duration_minutes: request.duration,
          include_answers: true,
          ...(request.instructions ? { instructions: request.instructions } : {}),
        });
      case 'feedback':
        return api(`/lessons/${request.lessonId}/feedback/draft`, 'POST', {
          recipient: request.recipient,
          ...(request.instructions ? { instructions: request.instructions } : {}),
        });
    }
  },
};
