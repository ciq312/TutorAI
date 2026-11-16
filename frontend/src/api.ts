const errors: Record<string, string> = {
  google_not_configured: 'На сервере не настроен Google OAuth.',
  integration_key_missing: 'На сервере отсутствует корректный ключ шифрования интеграций.',
  integration_key_invalid: 'Не удалось прочитать токены. Проверьте ключ шифрования сервера.',
  google_not_connected: 'Сначала подключите Google Calendar в настройках.',
  calendar_not_selected: 'Этот календарь не выбран в настройках.',
  calendar_homework_unavailable:
    'Нужно принятое ДЗ и занятие, привязанное к событию выбранного календаря Google.',
  calendar_changed:
    'Событие изменилось в Google. Закройте просмотр и подготовьте изменение заново.',
  approval_stale: 'ДЗ изменилось. Подготовьте предварительный просмотр заново.',
  approval_expired: 'Подтверждение истекло или отменено. Подготовьте просмотр заново.',
  results_stale: 'Заметки или черновик изменились. Сформируйте результаты заново.',
  lesson_notes_required: 'Сначала сохраните фактические итоги занятия.',
  telegram_not_configured: 'На сервере не задан токен Telegram-бота.',
  integration_reconnect_required: 'Проверьте права доступа или переподключите интеграцию.',
  integration_unavailable: 'Внешний сервис недоступен. Попробуйте позже.',
  event_not_teachable: 'Для занятия нужно активное событие с временем начала и окончания.',
  event_duration_invalid: 'Длительность занятия должна быть от 10 до 240 минут.',
  event_already_linked: 'Событие уже привязано к ученику.',
  curriculum_in_use:
    'Изменение затронет текущие темы учеников. Сначала снимите назначения этого КТП.',
  curriculum_not_reviewed: 'Сначала проверьте и сохраните темы КТП.',
  document_not_processed: 'Документ ещё не обработан. Запустите worker и обновите статус.',
  knowledge_search_unavailable: 'Поиск недоступен. Проверьте настройки embeddings.',
  delivery_still_sending:
    'Отправка ещё может выполняться. Проверьте Telegram и повторите через две минуты.',
  notification_stale: 'Уведомление устарело: занятие перенесено, отменено или изменены настройки.',
};
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api' + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    let code = '';
    try {
      const data = await response.json();
      code = data.detail?.code || '';
    } catch {}
    throw new Error(
      errors[code] ||
        (code === 'no_context'
          ? 'Для подготовки плана сначала добавьте занятие с заметками.'
          : response.status === 422
            ? 'Проверьте заполненные поля.'
            : response.status >= 500
              ? 'Сервис временно недоступен. Проверьте API и настройки модели.'
              : 'Не удалось выполнить запрос. Попробуйте ещё раз.'),
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
