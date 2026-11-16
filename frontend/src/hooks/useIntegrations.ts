import { useEffect, useState, useCallback } from 'react';
import {
  integrationApi,
  type IntegrationStatus,
  type GoogleCalendar,
  type CalendarSelection,
  type Delivery,
} from '../services/integrationApi';

export function useIntegrations() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [calendars, setCalendars] = useState<GoogleCalendar[]>([]);
  const [selected, setSelected] = useState<CalendarSelection[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [telegramUrl, setTelegramUrl] = useState('');
  const refresh = useCallback(async () => {
    const next = await integrationApi.status();
    setStatus(next);
    setSelected(next.calendars);
    const results = await Promise.allSettled([
      next.google_connected ? integrationApi.calendars() : Promise.resolve([]),
      integrationApi.deliveries(),
    ]);
    if (results[0].status === 'fulfilled') setCalendars(results[0].value);
    else throw results[0].reason;
    if (results[1].status === 'fulfilled') setDeliveries(results[1].value);
    else throw results[1].reason;
  }, []);
  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
  }, [refresh]);
  async function run(action: () => Promise<unknown>, message = 'Сохранено') {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
      await refresh();
      setNotice(message);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function toggle(id: string, checked: boolean) {
    setSelected((old) =>
      checked
        ? [...old, { calendar_id: id, mode: 'mixed' }]
        : old.filter((c) => c.calendar_id !== id),
    );
  }
  return {
    status,
    calendars,
    selected,
    setSelected,
    deliveries,
    busy,
    error,
    notice,
    telegramUrl,
    toggle,
    refresh: () => run(refresh, 'Обновлено'),
    connectGoogle: () =>
      run(async () => {
        const { url } = await integrationApi.connectGoogle();
        window.location.assign(url);
      }, ''),
    disconnectGoogle: () => run(integrationApi.disconnectGoogle, 'Google отключён'),
    saveCalendars: () => run(() => integrationApi.selectCalendars(selected)),
    sync: () => run(integrationApi.sync, 'Календарь синхронизирован'),
    connectTelegram: () =>
      run(async () => {
        const { url } = await integrationApi.connectTelegram();
        setTelegramUrl(url);
      }, 'Откройте бота и нажмите Start, затем проверьте подключение.'),
    checkTelegram: () => run(integrationApi.checkTelegram, 'Статус подключения обновлён'),
    disconnectTelegram: () =>
      run(async () => {
        await integrationApi.disconnectTelegram();
        setTelegramUrl('');
      }, 'Telegram отключён'),
    saveNotifications: (settings: IntegrationStatus['notifications']) =>
      run(() => integrationApi.notifications(settings)),
    retryDelivery: (key: string) =>
      run(() => integrationApi.retryDelivery(key), 'Повторная отправка запланирована'),
  };
}
