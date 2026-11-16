import { IntegrationSettings } from '../components/settings/IntegrationSettings';
import { AutomationSettings } from '../components/settings/AutomationSettings';
import type { Preferences } from '../hooks/usePreferences';
type Props = { preferences: Preferences; onSavePreferences: (value: Preferences) => void };
export function SettingsPage({ preferences, onSavePreferences }: Props) {
  return (
    <>
      <div className="mb-7">
        <h1>Настройки</h1>
        <p className="text-[12px] text-muted">Подготовка к занятиям и подключения.</p>
      </div>
      <AutomationSettings preferences={preferences} onSave={onSavePreferences} />
      <IntegrationSettings />
    </>
  );
}
