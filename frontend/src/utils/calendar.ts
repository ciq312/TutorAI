export function dayKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
export function monthDays(month: Date): Date[] {
  const start = new Date(month.getFullYear(), month.getMonth(), 1);
  const offset = (start.getDay() + 6) % 7;
  return Array.from(
    { length: 42 },
    (_, index) => new Date(month.getFullYear(), month.getMonth(), index - offset + 1),
  );
}
export function isUpcoming(scheduledAt: string, now: Date): boolean {
  return new Date(scheduledAt).getTime() > now.getTime();
}

/** A finite set of weekly appointments; preserve local wall-clock time across DST. */
export function weeklyDates(start: string, count: number): string[] {
  if (!Number.isInteger(count) || count < 1 || count > 8)
    throw new Error('Количество занятий должно быть от 1 до 8.');
  const first = new Date(start);
  if (Number.isNaN(first.getTime())) throw new Error('Укажите корректную дату занятия.');
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(first);
    date.setDate(first.getDate() + index * 7);
    return date.toISOString();
  });
}
