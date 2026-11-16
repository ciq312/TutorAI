import { ResultsEditor } from '../components/lessons/ResultsEditor';
import { CalendarHomework } from '../components/lessons/CalendarHomework';
import { useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CalendarDays,
  Clock3,
  Copy,
  MessageSquare,
  Plus,
  Sparkles,
} from 'lucide-react';
import { ui } from '../components/ui/styles';
import { LessonStatus } from '../components/lessons/LessonStatus';
import { DraftEditor } from '../components/lessons/DraftEditor';
import { OutcomesForm } from '../components/lessons/OutcomesForm';
import { LessonSchedule } from '../components/lessons/LessonSchedule';
import { useLessonWorkspace, type LessonTab } from '../hooks/useLessonWorkspace';
import type { Student, Lesson } from '../types';
const tabs: { key: LessonTab; label: string }[] = [
  { key: 'plan', label: 'Подготовка' },
  { key: 'outcomes', label: 'Итоги' },
  { key: 'homework', label: 'Новое ДЗ' },
  { key: 'student', label: 'Для ученика' },
  { key: 'next_plan', label: 'Следующий урок' },
];
type Props = {
  initialTab: LessonTab;
  lesson: Lesson;
  student: Student;
  lessons: Lesson[];
  onCommit: (lesson: Lesson) => void;
  onBack: () => void;
  onChat: () => void;
  onNext: () => void;
};
export function LessonPage({
  initialTab,
  lesson,
  student,
  lessons,
  onCommit,
  onBack,
  onChat,
  onNext,
}: Props) {
  const [tab, setTab] = useState<LessonTab>(initialTab);
  const { busy, error, notice, save, saveDraft, generate, acceptHomework, copy } =
    useLessonWorkspace({ lesson, student, onCommit });
  const previous = lessons
    .filter(
      (l) =>
        l.id !== lesson.id &&
        l.status !== 'cancelled' &&
        new Date(l.scheduled_at) < new Date(lesson.scheduled_at),
    )
    .sort((a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime())[0];
  return (
    <>
      <button className={ui.back} onClick={onBack}>
        <ArrowLeft size={15} />К календарю
      </button>
      <div className={ui['page-heading']}>
        <div>
          <div className="mb-3 flex items-center gap-3">
            <span className={ui.eyebrow + ' mb-0'}>КАРТОЧКА ЗАНЯТИЯ</span>
            <LessonStatus lesson={lesson} />
          </div>
          <h1>{lesson.topic}</h1>
          <p>
            {student.name} · {student.grade || 'Уровень не указан'}
          </p>
        </div>
        <button className={ui.secondary} onClick={onChat}>
          <MessageSquare size={15} />
          Обсудить в чате
        </button>
      </div>
      <div className="grid grid-cols-[minmax(0,1fr)_290px] items-start gap-6 max-[1100px]:grid-cols-1">
        <section className={ui.panel}>
          <div
            role="tablist"
            aria-label="Материалы занятия"
            className="mb-7 flex flex-wrap gap-2 border-b border-line pb-4"
          >
            {tabs.map((t) => (
              <button
                key={t.key}
                id={`tab-${t.key}`}
                role="tab"
                aria-selected={tab === t.key}
                aria-controls={`panel-${t.key}`}
                onClick={() => setTab(t.key)}
                className={`rounded-lg px-3 py-2 text-[11px] ${tab === t.key ? 'bg-[#403252] text-[#ddcaff]' : 'text-muted hover:bg-canvas'}`}
              >
                {t.label}
              </button>
            ))}
          </div>
          {error && (
            <p className={ui.error} role="alert">
              {error}
            </p>
          )}
          {notice && (
            <p
              role="status"
              className="rounded-xl border border-[#415c50] bg-[#25372f] p-3 text-[11px] text-[#b2d8c2]"
            >
              {notice}
            </p>
          )}
          <div key={tab} role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
            {tab === 'outcomes' ? (
              <>
                <OutcomesForm
                  lesson={lesson}
                  busy={busy || lesson.status === 'cancelled'}
                  onSave={save}
                />
                <ResultsEditor lesson={lesson} onCommit={onCommit} />
              </>
            ) : tab === 'student' ? (
              <>
                <h2>Только задания. Без решений.</h2>
                <p className="text-[11px] text-muted">
                  Здесь отображается принятое ДЗ — именно ту версию можно отправить ученику.
                </p>
                {lesson.homework ? (
                  <>
                    <div className="my-5 whitespace-pre-wrap rounded-xl border border-line bg-canvas/40 p-6 text-[13px] leading-8">
                      {lesson.homework}
                    </div>
                    <button className={ui.primary} onClick={() => void copy(lesson.homework!)}>
                      <Copy size={15} />
                      Скопировать для ученика
                    </button>
                    <p className="text-[10px] text-muted">
                      Отправьте текст ученику самостоятельно. Бот доставляет сообщения репетитору.
                    </p>
                    <CalendarHomework lesson={lesson} />
                  </>
                ) : (
                  <div className={ui.empty}>
                    <BookOpen />
                    <h3>Сначала примите домашнее задание</h3>
                    <button className={ui.secondary} onClick={() => setTab('homework')}>
                      Перейти к ДЗ <ArrowRight size={14} />
                    </button>
                  </div>
                )}
              </>
            ) : (
              <>
                {tab === 'plan' && previous?.homework && (
                  <details className="mb-6" open>
                    <summary>
                      Предыдущее ДЗ · {new Date(previous.scheduled_at).toLocaleDateString('ru-RU')}
                    </summary>
                    <p className="whitespace-pre-wrap text-[12px]">{previous.homework}</p>
                    {previous.materials?.homework?.answers && (
                      <details>
                        <summary>Решения для преподавателя</summary>
                        <p className="whitespace-pre-wrap">{previous.materials.homework.answers}</p>
                      </details>
                    )}
                  </details>
                )}
                {(tab === 'homework' || tab === 'next_plan' || tab === 'feedback') &&
                  !lesson.notes && (
                    <div className={ui.difficulty}>
                      Сначала запишите фактические итоги занятия. Без заметок материал может
                      опираться только на тему и прошлую историю.{' '}
                      <button className="text-accent underline" onClick={() => setTab('outcomes')}>
                        Записать итоги
                      </button>
                    </div>
                  )}
                <DraftEditor
                  key={tab}
                  kind={tab}
                  draft={lesson.materials?.[tab]}
                  topic={
                    tab === 'next_plan'
                      ? lesson.materials?.next_topic || lesson.topic
                      : lesson.topic
                  }
                  duration={tab === 'homework' ? 20 : lesson.duration_minutes || 60}
                  busy={busy || lesson.status === 'cancelled'}
                  accepted={lesson.homework}
                  onGenerate={(options) => generate(tab, options)}
                  onSave={(draft) => saveDraft(tab, draft)}
                  onAccept={tab === 'homework' ? acceptHomework : undefined}
                  onCopy={(text) => void copy(text)}
                />
                {tab === 'next_plan' && (
                  <div className="mt-7 rounded-xl border border-line p-5">
                    <h3 className="mt-0 text-[13px]">Перенести план в следующее занятие</h3>
                    <p className="text-[11px] text-muted">
                      Создайте следующее занятие. Сохранённый план будет добавлен к нему после
                      создания.
                    </p>
                    <button
                      className={ui.secondary}
                      onClick={onNext}
                      disabled={busy || lesson.status === 'cancelled'}
                    >
                      <Plus size={15} />
                      Назначить следующий урок
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </section>
        <aside className="space-y-5">
          <section className={ui.panel}>
            <div className="flex items-center gap-2 text-accent">
              <CalendarDays size={17} />
              <h2 className="text-[14px]">
                {new Date(lesson.scheduled_at).toLocaleDateString('ru-RU', {
                  day: 'numeric',
                  month: 'long',
                  weekday: 'short',
                })}
              </h2>
            </div>
            <p className="flex items-center gap-2 text-[12px] text-muted">
              <Clock3 size={14} />
              {new Date(lesson.scheduled_at).toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit',
              })}{' '}
              · {lesson.duration_minutes || 60} мин
            </p>
            <div className="mt-5 border-t border-line pt-4 text-[11px] text-muted">
              <strong className="text-[#d7cce8]">Цель ученика</strong>
              <p>{student.goals || 'Цель пока не указана'}</p>
            </div>
            <LessonSchedule lesson={lesson} busy={busy} onSave={save} />
            <label className="mt-4 flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                className="w-auto"
                disabled={busy}
                checked={lesson.notifications_enabled !== false}
                onChange={(e) => void save({ notifications_enabled: e.target.checked })}
              />
              Сообщения об этом занятии
            </label>
          </section>
          <section className="rounded-2xl border border-[#493b60] bg-[#292334] p-5">
            <Sparkles size={20} className="text-accent" />
            <h3 className="text-[13px]">Подготовка: {lesson.preparation_minutes ?? 30} минут</h3>
            <p className="text-[11px] text-muted">
              Материалы создаются в карточке. Доставку сохранённого брифа и результатов включите в
              настройках Telegram.
            </p>
          </section>
        </aside>
      </div>
    </>
  );
}
