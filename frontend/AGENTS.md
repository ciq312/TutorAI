# Frontend conventions

Follow the user's requested SOLID, YAGNI, DRY and KISS principles.

- Keep App responsible for composing the layout and selecting pages.
- Put page-specific UI in pages/, and reusable domain UI in components/.
- Components receive typed data and callbacks through props; do not issue HTTP requests from presentation components.
- Keep stateful workflows in focused hooks; endpoint paths and payload mapping belong in services/tutorApi.ts.
- Calendar is the default entry point; all teaching-material actions must use the shared lesson workspace. Keep free chat available as a separate tab.
- Draft homework and accepted homework are distinct. Never include teacher answers in the student-facing copy, and never mark a lesson completed just because its date is in the past.
- Do not imply that Telegram, calendar synchronization, or scheduled preparation is active until backed by a working integration or server scheduler.
- Keep domain types in types.ts and pure helpers in utils/.
- Use real API data only; never seed demo students or substitute generated sample answers. Use empty states when there are no records.
- Use components/ui/DateTimePicker.tsx for date/time selection instead of native date or datetime-local inputs. Creation dialogs open centered in the viewport.
- Reuse actual repeated behavior. Do not add speculative abstractions, generic repositories, dependency injection frameworks, or state libraries without a concrete need.
- Keep new code formatted with the project Prettier configuration. Run npm run build after structural changes.
- Use Tailwind CSS v4 utilities for component styles. Keep palette tokens in src/style.css under @theme and only global element defaults under @layer base.
- Reuse repeated utility sets from components/ui/styles.ts; keep complete class names in source so Tailwind can detect them. Do not construct class names from string fragments.

- Keep the header limited to logo, navigation tabs, and settings. The conversation student picker belongs inside the chat tab, not in the global header.
- Student creation belongs in the Students tab. The chat student picker only selects existing students.
