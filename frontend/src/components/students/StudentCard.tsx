import { ArrowUpRight, BookOpen, ChevronRight } from 'lucide-react';
import type { Student } from '../../types';
import { initials } from '../../utils/format';
const avatarColors = [
  'w-[51px] h-[51px] inline-flex items-center justify-center shrink-0 rounded-[17px] bg-[#453b5e] text-[#d5c4ff] font-[750] text-[17px] max-[760px]:w-[43px] max-[760px]:h-[43px] max-[760px]:text-[14px] max-[760px]:rounded-[13px]',
  'w-[51px] h-[51px] inline-flex items-center justify-center shrink-0 rounded-[17px] bg-[#2c4548] text-[#aed2cb] font-[750] text-[17px] max-[760px]:w-[43px] max-[760px]:h-[43px] max-[760px]:text-[14px] max-[760px]:rounded-[13px]',
  'w-[51px] h-[51px] inline-flex items-center justify-center shrink-0 rounded-[17px] bg-[#4a3d3f] text-[#edc0b0] font-[750] text-[17px] max-[760px]:w-[43px] max-[760px]:h-[43px] max-[760px]:text-[14px] max-[760px]:rounded-[13px]',
  'w-[51px] h-[51px] inline-flex items-center justify-center shrink-0 rounded-[17px] bg-[#37415c] text-[#b7cafa] font-[750] text-[17px] max-[760px]:w-[43px] max-[760px]:h-[43px] max-[760px]:text-[14px] max-[760px]:rounded-[13px]',
];
type Props = { student: Student; index: number; onOpen: (student: Student) => void };
export function StudentCard({ student: s, index: i, onOpen }: Props) {
  return (
    <button
      className="bg-surface [border:1px_solid_#343642] rounded-[13px] p-[21px_21px_0] text-left min-w-0 transition-colors duration-150 motion-reduce:transition-none hover:border-[#8d76bb] hover:bg-[#292a39] [&_h3]:text-[14px] [&_h3]:tracking-[-.2px] [&_h3]:m-[0_0_7px] [&_h3]:wrap-anywhere max-[760px]:p-[17px_15px_0] max-[760px]:[&_h3]:text-[12px]"
      onClick={() => onOpen(s)}
    >
      <div className="flex items-center justify-between mb-[18px] [&>svg]:text-[#77798f]">
        <span className={avatarColors[i % avatarColors.length]}>{initials(s.name)}</span>
        <ArrowUpRight size={19} />
      </div>
      <h3>{s.name}</h3>
      <span className="inline-block text-[9px] text-[#a8a8bb] bg-[#30323f] p-[4px_7px] rounded-[4px]">
        {s.grade || 'Класс не указан'}
      </span>
      <div className="mt-[22px] [&>span]:text-[8px] [&>span]:tracking-[1px] [&>span]:text-[#7f8298] [&>span]:font-[750] [&_p]:text-[10px] [&_p]:text-[#b5b5c6] [&_p]:leading-[1.9] [&_p]:min-h-[56px] [&_p]:wrap-anywhere [&_p]:m-[7px_0_17px] max-[760px]:[&_p]:text-[10px]">
        <span>ЦЕЛЬ ОБУЧЕНИЯ</span>
        <p>{s.goals || 'Добавьте цель в профиле ученика'}</p>
      </div>
      <div className="flex items-center gap-[7px] [border-top:1px_solid_#363845] p-[15px_0] text-[#8e91a7] text-[8px] [&_svg:last-child]:ml-auto max-[760px]:text-[8px] max-[760px]:gap-[4px] max-[760px]:[&_svg]:w-[12px]">
        <BookOpen size={15} />
        <span>Открыть историю занятий</span>
        <ChevronRight size={15} />
      </div>
    </button>
  );
}
