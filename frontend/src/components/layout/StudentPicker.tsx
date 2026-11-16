import { Users } from 'lucide-react';
import type { Student } from '../../types';
type Props = {
  students: Student[];
  selected: Student | null;
  loading: boolean;
  onSelect: (student: Student | null) => void;
};
export function StudentPicker({ students, selected, loading, onSelect }: Props) {
  return (
    <div className="flex min-w-0 items-center gap-2">
      <div className="flex min-w-0 items-center gap-2 rounded-xl border border-[#494052] bg-[#282532] pl-3">
        <Users size={15} className="shrink-0 text-accent" />
        <select
          aria-label="Выбрать ученика"
          disabled={loading && !students.length}
          value={selected?.id ?? ''}
          onChange={(e) => onSelect(students.find((s) => s.id === e.target.value) ?? null)}
          className="m-0 w-[230px] min-w-0 border-0 bg-transparent py-2.5 text-[12px] focus:shadow-none max-[500px]:w-[150px]"
        >
          <option value="">{loading ? 'Загрузка…' : 'Выберите ученика'}</option>
          {students.map((s) => (
            <option value={s.id} key={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
