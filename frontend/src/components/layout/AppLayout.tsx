import {
  CalendarDays,
  BookOpen,
  GraduationCap,
  MessageSquare,
  Settings,
  Sparkles,
  Users,
} from 'lucide-react';
import type { ReactNode } from 'react';
import type { Page } from '../../types';
type Props = {
  page: Page;
  setPage: (page: Page) => void;
  children: ReactNode;
};
const tabs = [
  { page: 'calendar', label: 'Календарь', icon: CalendarDays },
  { page: 'chat', label: 'Чат', icon: MessageSquare },
  { page: 'students', label: 'Ученики', icon: Users },
  { page: 'knowledge', label: 'База знаний', icon: BookOpen },
] as const;
export function AppLayout({ page, setPage, children }: Props) {
  return (
    <div className="min-h-dvh bg-canvas">
      <header className="sticky top-0 z-20 grid min-h-[84px] grid-cols-[1fr_auto_1fr] items-center gap-4 border-b border-line bg-canvas/95 px-8 backdrop-blur-xl max-[760px]:grid-cols-[1fr_auto] max-[760px]:gap-3 max-[760px]:px-4 max-[760px]:py-3">
        <button
          onClick={() => setPage('calendar')}
          className="flex w-fit items-center gap-2 text-[20px] font-extrabold tracking-tight max-[500px]:text-[16px]"
        >
          <span className="grid size-9 -rotate-6 place-items-center rounded-xl bg-primary text-primary-foreground">
            <GraduationCap size={23} />
          </span>
          my tutor<span className="text-[11px] text-accent">ai</span>
        </button>
        <nav
          aria-label="Основная навигация"
          className="flex justify-center gap-1 max-[760px]:col-span-2 max-[760px]:row-start-2 max-[760px]:w-full"
        >
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const active =
              page === tab.page ||
              (tab.page === 'calendar' && page === 'lesson') ||
              (tab.page === 'students' && page === 'student');
            return (
              <button
                key={tab.page}
                onClick={() => setPage(tab.page)}
                aria-current={active ? 'page' : undefined}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 max-[500px]:px-2 max-[500px]:text-[10px] text-[12px] ${active ? 'bg-[#332b44] text-[#c6b1ff]' : 'text-muted hover:bg-surface'}`}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </nav>
        <div className="flex items-center justify-end gap-4 text-[10px] text-muted">
          <button
            aria-label="Настройки"
            onClick={() => setPage('settings')}
            className={`rounded-lg p-2 ${page === 'settings' ? 'text-accent' : 'hover:text-accent'}`}
          >
            <Settings size={18} />
          </button>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1450px] px-8 py-7 max-[760px]:px-4">{children}</main>
      <footer className="mx-auto flex max-w-[1450px] items-center justify-between px-8 pb-5 text-[9px] text-muted">
        <span>my tutor ai</span>
        <span className="flex items-center gap-2">
          Больше внимания каждому ученику <Sparkles size={11} />
        </span>
      </footer>
    </div>
  );
}
