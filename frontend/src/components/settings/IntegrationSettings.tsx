import { type FormEvent } from 'react';
import { useIntegrations } from '../../hooks/useIntegrations';
import { ui } from '../ui/styles';
export function IntegrationSettings() {
  const vm = useIntegrations();
  const s = vm.status;
  function saveNotifications(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    void vm.saveNotifications({
      brief_enabled: data.has('brief'),
      results_enabled: data.has('results'),
      reminder_enabled: data.has('reminder'),
      before_minutes: Number(data.get('before')),
      after_minutes: Number(data.get('after')),
      timezone: String(data.get('timezone')),
    });
  }
  return (
    <div className="mt-5 space-y-5">
      {vm.error && (
        <p role="alert" className={ui.error}>
          {vm.error}
        </p>
      )}
      {vm.notice && (
        <p role="status" className="text-accent">
          {vm.notice}
        </p>
      )}
      <div className="grid gap-5 md:grid-cols-2">
        <section className={ui.panel}>
          <h2>Google Calendar</h2>
          <p className="text-sm text-muted">{s?.google_connected ? 'Подключён' : 'Не подключён'}</p>
          {s && !s.google_configured && (
            <p className={ui.difficulty}>
              Для подключения укажите Google OAuth и ключ шифрования в настройках сервера.
              Инструкция — в README проекта.
            </p>
          )}
          {s?.google_connected ? (
            <>
              <p className="text-xs text-muted">
                Выберите календари. События появятся во входящих календаря, где их можно связать с
                учеником.
              </p>
              {vm.calendars.map((c) => {
                const chosen = vm.selected.find((x) => x.calendar_id === c.id);
                return (
                  <div key={c.id} className="my-3 rounded-xl border border-line p-3">
                    <label className="flex items-center gap-2">
                      <input
                        className="w-auto"
                        type="checkbox"
                        checked={!!chosen}
                        onChange={(e) => vm.toggle(c.id, e.target.checked)}
                      />
                      {c.summary}
                    </label>
                    {chosen && (
                      <label>
                        Назначение
                        <select
                          value={chosen.mode}
                          onChange={(e) =>
                            vm.setSelected((old) =>
                              old.map((x) =>
                                x.calendar_id === c.id
                                  ? { ...x, mode: e.target.value as 'mixed' | 'teaching' }
                                  : x,
                              ),
                            )
                          }
                        >
                          <option value="mixed">Личный и рабочий — выбирать занятия вручную</option>
                          <option value="teaching">Занятия с учениками</option>
                        </select>
                      </label>
                    )}
                    {!['owner', 'writer'].includes(c.access_role) && (
                      <p className="text-xs text-muted">
                        Только чтение: записать ДЗ в этот календарь нельзя.
                      </p>
                    )}
                  </div>
                );
              })}
              <div className="flex flex-wrap gap-2">
                <button
                  disabled={vm.busy}
                  className={ui.primary}
                  onClick={() => void vm.saveCalendars()}
                >
                  Сохранить выбор
                </button>
                <button disabled={vm.busy} className={ui.secondary} onClick={() => void vm.sync()}>
                  Синхронизировать
                </button>
                <button
                  disabled={vm.busy}
                  className={ui.secondary}
                  onClick={() => void vm.disconnectGoogle()}
                >
                  Отключить
                </button>
              </div>
              {s.last_sync && (
                <p className="text-xs text-muted">
                  Последняя синхронизация: {new Date(s.last_sync).toLocaleString('ru-RU')}
                </p>
              )}
              {s.sync_error && (
                <p className={ui.error}>
                  Не удалось синхронизировать. Проверьте подключение Google.
                </p>
              )}
            </>
          ) : (
            <button
              className={ui.primary}
              disabled={vm.busy || !s?.google_configured}
              onClick={() => void vm.connectGoogle()}
            >
              Подключить Google
            </button>
          )}
        </section>
        <section className={ui.panel}>
          <h2>Telegram для репетитора</h2>
          <p className="text-sm text-muted">
            {s?.telegram_connected ? 'Подключён личный чат' : 'Не подключён'}
          </p>
          <p className="text-xs text-muted">
            Бриф перед уроком и проверенные результаты после него. Ученикам и родителям бот
            сообщения не отправляет.
          </p>
          {s && !s.telegram_configured && (
            <p className={ui.difficulty}>
              Укажите TELEGRAM_BOT_TOKEN на сервере и запустите worker.
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            <button
              className={ui.primary}
              disabled={vm.busy || !s?.telegram_configured}
              onClick={() => void vm.connectTelegram()}
            >
              {s?.telegram_connected ? 'Переподключить бота' : 'Подключить бота'}
            </button>
            <button
              className={ui.secondary}
              disabled={vm.busy || !s?.telegram_configured}
              onClick={() => void vm.checkTelegram()}
            >
              Проверить подключение
            </button>
            {s?.telegram_connected && (
              <button
                className={ui.secondary}
                disabled={vm.busy}
                onClick={() => void vm.disconnectTelegram()}
              >
                Отключить
              </button>
            )}
          </div>
          {vm.telegramUrl && (
            <p>
              <a
                className="text-accent underline"
                target="_blank"
                rel="noreferrer"
                href={vm.telegramUrl}
              >
                Открыть Telegram и нажать Start
              </a>
              <span className="block text-xs text-muted">Ссылка действует 10 минут.</span>
            </p>
          )}
        </section>
      </div>
      {s && (
        <section className={ui.panel}>
          <h2>Доставка сообщений</h2>
          <p className="text-xs text-muted">
            {s.worker_heartbeat
              ? `Worker: последнее обновление ${new Date(s.worker_heartbeat).toLocaleString('ru-RU')}`
              : 'Worker ещё не запускался. Запустите python -m app.worker или сервис worker в Docker Compose.'}
          </p>
          {s.worker_heartbeat && Date.now() - Date.parse(s.worker_heartbeat) > 180000 && (
            <p className={ui.difficulty}>
              Worker давно не обновлялся. Автоматическая доставка может не работать.
            </p>
          )}
          {s.worker_error && (
            <p className={ui.error}>
              Фоновая задача завершилась с ошибкой. Проверьте подключения и серверный журнал.
            </p>
          )}
          <button className={ui.secondary} disabled={vm.busy} onClick={() => void vm.refresh()}>
            Обновить статус
          </button>
          <form key={JSON.stringify(s.notifications)} onSubmit={saveNotifications} className="mt-5">
            <div className="flex flex-wrap gap-5">
              {[
                ['brief', 'Бриф перед занятием', s.notifications.brief_enabled],
                ['results', 'Проверенные результаты', s.notifications.results_enabled],
                ['reminder', 'Напоминание заполнить итоги', s.notifications.reminder_enabled],
              ].map(([name, label, checked]) => (
                <label key={String(name)} className="flex items-center gap-2">
                  <input
                    className="w-auto"
                    type="checkbox"
                    name={String(name)}
                    defaultChecked={Boolean(checked)}
                  />
                  {label}
                </label>
              ))}
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <label>
                Бриф за, минут
                <input
                  type="number"
                  min={0}
                  max={10080}
                  name="before"
                  defaultValue={s.notifications.before_minutes}
                  required
                />
              </label>
              <label>
                Напомнить после окончания, минут
                <input
                  type="number"
                  min={0}
                  max={1440}
                  name="after"
                  defaultValue={s.notifications.after_minutes}
                  required
                />
              </label>
              <label>
                Часовой пояс
                <input
                  name="timezone"
                  defaultValue={s.notifications.timezone}
                  required
                  placeholder="Europe/Minsk"
                />
              </label>
            </div>
            <button disabled={vm.busy} className={ui.primary}>
              Сохранить на сервере
            </button>
          </form>
          {!!vm.deliveries.length && (
            <details className="mt-5">
              <summary>Последние доставки</summary>
              {vm.deliveries.map((d) => (
                <div key={d.key} className="my-3 rounded-lg border border-line p-3 text-xs">
                  <p>
                    {d.student_name} · {new Date(d.scheduled_at).toLocaleString('ru-RU')} ·{' '}
                    {
                      (
                        { brief: 'Бриф', results: 'Результаты', reminder: 'Напоминание' } as Record<
                          string,
                          string
                        >
                      )[d.kind]
                    }{' '}
                    ·{' '}
                    {(
                      {
                        sent: 'Доставлено',
                        queued: 'В очереди',
                        sending: 'Отправка не подтверждена',
                        uncertain: 'Доставка не подтверждена',
                        cancelled: 'Отменено',
                      } as Record<string, string>
                    )[d.status] || d.status}
                  </p>
                  {['uncertain', 'sending'].includes(d.status) && (
                    <>
                      <p>
                        Сообщение могло дойти. Перед повтором проверьте Telegram — возможен дубль.
                      </p>
                      <button
                        disabled={vm.busy}
                        className={ui.secondary}
                        onClick={() => void vm.retryDelivery(d.key)}
                      >
                        Повторить отправку
                      </button>
                    </>
                  )}
                </div>
              ))}
            </details>
          )}
        </section>
      )}
    </div>
  );
}
