import { KnowledgePage } from './pages/KnowledgePage';
import { usePreferences } from './hooks/usePreferences';
import { LessonPage } from './pages/LessonPage';
import { ChatPage } from './pages/ChatPage';
import { CalendarPage } from './pages/CalendarPage';
import { ui } from './components/ui/styles';
import { Check, X } from 'lucide-react';
import { useWorkspace } from './hooks/useWorkspace';
import { AppLayout } from './components/layout/AppLayout';
import { RecordDialog } from './components/RecordDialog';
import { StudentsPage } from './pages/StudentsPage';
import { StudentPage } from './pages/StudentPage';
import { SettingsPage } from './pages/SettingsPage';
export default function App() {
  const workspace = useWorkspace();
  const { preferences, save: savePreferences } = usePreferences();
  const { page, setPage, error, setError, notice } = workspace;
  return (
    <>
      <AppLayout {...workspace}>
        {error && (
          <div role="alert" className={ui['error']}>
            {error}
            <button onClick={() => setError('')} aria-label="Закрыть ошибку">
              <X size={16} />
            </button>
          </div>
        )}
        <div hidden={page !== 'chat'}>
          <ChatPage
            students={workspace.students}
            loading={workspace.loading}
            onSelect={workspace.selectStudent}
            selected={workspace.selected}
            onHistory={() => setPage('student')}
            onCalendar={() => setPage('calendar')}
          />
        </div>
        <div hidden={page !== 'calendar'}>
          <CalendarPage
            students={workspace.students}
            selected={workspace.selected}
            enabled={page === 'calendar'}
            revision={workspace.calendarRevision}
            onCreate={(day) => {
              workspace.setLessonDate(day + 'T16:00');
              workspace.setModal('lesson');
            }}
            onImported={workspace.importCalendarLesson}
            onOpenLesson={workspace.openLesson}
          />
        </div>
        {page === 'lesson' && workspace.openedLesson && workspace.selected && (
          <LessonPage
            key={workspace.openedLesson.id + workspace.lessonTab}
            initialTab={workspace.lessonTab}
            lesson={workspace.openedLesson}
            student={workspace.selected}
            lessons={workspace.lessons}
            onCommit={workspace.commitLesson}
            onBack={() => setPage('calendar')}
            onChat={() => setPage('chat')}
            onNext={() => workspace.scheduleNext(workspace.openedLesson!)}
          />
        )}
        {page === 'knowledge' && <KnowledgePage students={workspace.students} />}
        {page === 'students' && <StudentsPage {...workspace} />}
        {page === 'student' && <StudentPage {...workspace} />}
        {page === 'settings' && (
          <SettingsPage
            {...workspace}
            preferences={preferences}
            onSavePreferences={savePreferences}
          />
        )}
      </AppLayout>
      <RecordDialog {...workspace} defaultPreparationMinutes={preferences.preparationMinutes} />
      {notice && (
        <div
          className="fixed bottom-[25px] left-[50%] [transform:translateX(-50%)] bg-[#393147] [border:1px_solid_#7a669b] p-[15px_22px] rounded-[12px] shadow-[0_8px_50px_#0005] flex items-center gap-[12px] z-[5] text-[12px] max-w-[90vw]"
          role="status"
        >
          <Check size={17} />
          {notice}
        </div>
      )}
    </>
  );
}
