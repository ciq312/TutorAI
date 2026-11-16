import test from 'node:test';
import assert from 'node:assert/strict';
import { dayKey, monthDays, isUpcoming } from '../src/utils/calendar.ts';

test('month grid starts on Monday and covers leap day', () => {
  const days = monthDays(new Date(2024, 1, 1));
  assert.equal(days.length, 42);
  assert.equal(days[0].getDay(), 1);
  assert.equal(new Set(days.map(dayKey)).size, 42);
  assert.ok(days.some((day) => dayKey(day) === '2024-02-29'));
});
test('month grid covers year boundaries in local time', () => {
  const days = monthDays(new Date(2027, 0, 1));
  assert.ok(days.some((day) => dayKey(day) === '2026-12-28'));
  assert.ok(days.some((day) => dayKey(day) === '2027-01-31'));
});
test('future and past compare exact instants, including timezone offsets', () => {
  const now = new Date('2026-11-15T12:00:00Z');
  assert.equal(isUpcoming('2026-11-15T15:01:00+03:00', now), true);
  assert.equal(isUpcoming('2026-11-15T15:00:00+03:00', now), false);
  assert.equal(isUpcoming('2026-11-15T14:59:00+03:00', now), false);
});

test('weekly appointments cross month and year boundaries', async () => {
  const { weeklyDates } = await import('../src/utils/calendar.ts');
  const dates = weeklyDates(new Date(2026, 11, 28, 16, 0).toISOString(), 4).map(
    (date) => new Date(date),
  );
  assert.equal(dates.length, 4);
  assert.equal(dayKey(dates[1]), '2027-01-04');
  assert.ok(dates.every((date) => date.getHours() === 16));
  assert.throws(() => weeklyDates('invalid', 4));
  assert.throws(() => weeklyDates(new Date().toISOString(), 9));
});
