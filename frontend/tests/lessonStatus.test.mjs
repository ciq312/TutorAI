import test from 'node:test';
import assert from 'node:assert/strict';
import { lessonStatus } from '../src/utils/lessonStatus.ts';
const now = new Date('2026-11-15T12:00:00Z');
const lesson = {
  scheduled_at: '2026-11-14T12:00:00Z',
  homework: null,
  status: 'scheduled',
  materials: {},
};
test('passing time never marks a lesson as actually completed', () => {
  assert.equal(lessonStatus(lesson, now).label, 'Ожидаются итоги');
  assert.equal(lessonStatus({ ...lesson, status: 'completed' }, now).label, 'Итоги сохранены');
});
test('draft and accepted homework have different states', () => {
  const draft = { ...lesson, status: 'completed', materials: { homework: { text: 'Задания' } } };
  assert.equal(lessonStatus(draft, now).label, 'ДЗ на проверке');
  assert.equal(lessonStatus({ ...draft, homework: 'Задания' }, now).label, 'Завершено');
  assert.equal(lessonStatus({ ...draft, homework: 'Старое ДЗ' }, now).label, 'ДЗ на проверке');
});
test('cancellation takes priority over saved material', () => {
  assert.equal(
    lessonStatus({ ...lesson, status: 'cancelled', materials: { plan: { text: 'План' } } }, now)
      .label,
    'Отменено',
  );
});
