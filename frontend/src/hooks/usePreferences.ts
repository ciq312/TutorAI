import { useState } from 'react';
const key = 'tutor-preferences';
export type Preferences = { preparationMinutes: number; outcomesReminderMinutes: number };
const defaults: Preferences = { preparationMinutes: 30, outcomesReminderMinutes: 15 };
function read(): Preferences {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '{}');
    return {
      preparationMinutes:
        Number.isInteger(value.preparationMinutes) &&
        value.preparationMinutes >= 0 &&
        value.preparationMinutes <= 10080
          ? value.preparationMinutes
          : 30,
      outcomesReminderMinutes:
        Number.isInteger(value.outcomesReminderMinutes) &&
        value.outcomesReminderMinutes >= 0 &&
        value.outcomesReminderMinutes <= 1440
          ? value.outcomesReminderMinutes
          : 15,
    };
  } catch {
    return defaults;
  }
}
export function usePreferences() {
  const [preferences, setPreferences] = useState(read);
  function save(value: Preferences) {
    localStorage.setItem(key, JSON.stringify(value));
    setPreferences(value);
  }
  return { preferences, save };
}
