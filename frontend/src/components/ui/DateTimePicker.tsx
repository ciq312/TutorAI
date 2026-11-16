import { useId, useRef, useState } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react';
import { dayKey, monthDays } from '../../utils/calendar';

type Props = { name: string; defaultValue: string; required?: boolean; disabled?: boolean };
export function DateTimePicker({ name, defaultValue, required, disabled }: Props) {
  const trigger = useRef<HTMLButtonElement>(null);
  const id = useId();
  const initial = new Date(defaultValue);
  const valid = Number.isNaN(initial.getTime()) ? new Date() : initial;
  const [selected, setSelected] = useState(() => dayKey(valid));
  const [month, setMonth] = useState(() => new Date(valid.getFullYear(), valid.getMonth(), 1));
  const [hour, setHour] = useState(() => String(valid.getHours()).padStart(2, '0'));
  const [minute, setMinute] = useState(() => String(valid.getMinutes()).padStart(2, '0'));
  const [open, setOpen] = useState(false);
  const today = dayKey(new Date());
  function move(offset: number) {
    setMonth((current) => new Date(current.getFullYear(), current.getMonth() + offset, 1));
  }
  return (
    <div
      className="mt-2"
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
      }}
      onKeyDown={(e) => {
        if (e.key === 'Escape' && open) {
          e.preventDefault();
          e.stopPropagation();
          setOpen(false);
        }
      }}
    >
      <input
        type="hidden"
        name={name}
        value={`${selected}T${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`}
        disabled={disabled}
      />
      <button
        ref={trigger}
        type="button"
        disabled={disabled}
        aria-expanded={open}
        aria-controls={id}
        aria-label="Выбрать дату занятия"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between rounded-lg border border-[#41404f] bg-[#1d1f2a] px-3 py-3 text-left text-[12px] text-[#e8e4f4] hover:border-accent"
      >
        <span>
          {new Date(selected + 'T12:00:00').toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
          })}
        </span>
        <CalendarDays size={17} className="text-accent" />
      </button>
      {open && (
        <div
          id={id}
          aria-label="Календарь выбора даты"
          className="mt-2 rounded-xl border border-[#534462] bg-[#25222f] p-3"
        >
          <div className="mb-3 flex items-center justify-between">
            <button
              type="button"
              aria-label="Предыдущий месяц"
              onClick={() => move(-1)}
              className="rounded-lg p-2 text-accent hover:bg-[#3c304d]"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-[12px] font-semibold capitalize" aria-live="polite">
              {month.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
            </span>
            <button
              type="button"
              aria-label="Следующий месяц"
              onClick={() => move(1)}
              className="rounded-lg p-2 text-accent hover:bg-[#3c304d]"
            >
              <ChevronRight size={16} />
            </button>
          </div>
          <div className="grid grid-cols-7 gap-1">
            {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((day) => (
              <span key={day} className="py-1 text-center text-[9px] text-muted">
                {day}
              </span>
            ))}
            {monthDays(month).map((date) => {
              const key = dayKey(date);
              return (
                <button
                  key={key}
                  type="button"
                  aria-label={date.toLocaleDateString('ru-RU', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                  })}
                  aria-pressed={selected === key}
                  onClick={() => {
                    setSelected(key);
                    setMonth(new Date(date.getFullYear(), date.getMonth(), 1));
                    setOpen(false);
                    trigger.current?.focus();
                  }}
                  className={`aspect-square rounded-lg text-[11px] hover:bg-[#51405f] ${selected === key ? 'bg-primary text-primary-foreground' : date.getMonth() !== month.getMonth() ? 'text-[#696377]' : 'text-[#d7cde5]'} ${today === key ? 'ring-1 ring-inset ring-accent' : ''}`}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>
          <button
            type="button"
            className="mt-2 px-2 py-1 text-[10px] text-accent"
            onClick={() => {
              setSelected(today);
              setMonth(new Date());
              setOpen(false);
              trigger.current?.focus();
            }}
          >
            Сегодня
          </button>
        </div>
      )}
      <div className="mt-3 flex items-center gap-2">
        <span className="mr-2 text-[10px] text-muted">Время</span>
        <input
          aria-label="Часы"
          type="number"
          min={0}
          max={23}
          required={required}
          disabled={disabled}
          value={hour}
          onChange={(e) => setHour(e.target.value)}
          onBlur={() => {
            if (hour !== '') setHour(hour.padStart(2, '0'));
          }}
          className="m-0 w-[65px] py-2 text-center"
        />
        <span className="text-muted">:</span>
        <input
          aria-label="Минуты"
          type="number"
          min={0}
          max={59}
          required={required}
          disabled={disabled}
          value={minute}
          onChange={(e) => setMinute(e.target.value)}
          onBlur={() => {
            if (minute !== '') setMinute(minute.padStart(2, '0'));
          }}
          className="m-0 w-[65px] py-2 text-center"
        />
        <span className="text-[9px] text-muted">
          {Intl.DateTimeFormat().resolvedOptions().timeZone}
        </span>
      </div>
    </div>
  );
}
