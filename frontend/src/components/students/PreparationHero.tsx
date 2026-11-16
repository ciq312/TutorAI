import { ArrowUpRight, BookOpen, Check, Sparkles } from 'lucide-react';
export function PreparationHero({ onPrepare }: { onPrepare: () => void }) {
  return (
    <section className="relative overflow-hidden flex justify-between min-h-[254px] [border:1px_solid_#443b60] [background:radial-gradient(ellipse_at_82%_65%,#59428088,transparent_47%),linear-gradient(115deg,#292637,#322a47)] rounded-[16px] mb-[35px] p-[29px_32px] [&_h2]:text-[24px] [&_h2]:tracking-[-.6px] [&_h2]:font-[750] [&_h2]:leading-[1.55] [&_h2]:m-[15px_0_9px] [&_h2_span]:text-[#c4b1f3] [&_p]:text-[#a9a2bb] [&_p]:text-[11px] [&_p]:leading-[1.9] [&_p]:m-0 min-[1500px]:min-h-[280px] max-[1150px]:p-[25px] max-[1150px]:[&_h2]:text-[20px] max-[1150px]:[&_p_br]:hidden max-[760px]:min-h-[265px] max-[760px]:p-[23px] max-[760px]:[&_h2]:text-[21px] max-[760px]:[&_p]:max-w-[270px]">
      <div className="z-[1] max-[760px]:max-w-[100%]">
        <span className="inline-flex items-center gap-[7px] bg-[#8971ca21] text-[#c3b2f6] [border:1px_solid_#8b70c638] rounded-[6px] text-[8px] tracking-[1px] p-[7px_9px] font-[750]">
          <Sparkles size={13} /> AI ДЛЯ ПРЕПОДАВАТЕЛЯ
        </span>
        <h2>
          Вы преподаёте.
          <br />
          <span>О подготовке позаботимся вместе.</span>
        </h2>
        <p>
          История занятий превращается в персональный план.
          <br />
          Остаётся добавить ваш опыт и немного вдохновения.
        </p>
        <button
          className="flex items-center gap-[10px] bg-transparent border-0 p-0 text-[#ddd0ff] font-bold text-[11px] mt-[22px] max-[760px]:mt-[25px]"
          onClick={onPrepare}
        >
          Подготовиться к занятию <ArrowUpRight size={17} />
        </button>
      </div>
      <div
        className="relative w-[275px] shrink-0 self-stretch min-[1500px]:mr-[50px] max-[1150px]:w-[210px] max-[1150px]:[transform:scale(.9)] max-[1150px]:origin-right max-[760px]:hidden"
        aria-hidden="true"
      >
        <div className="absolute [border:1px_solid_#b699f436] w-[218px] h-[108px] rounded-full top-[56px] left-[20px] [transform:rotate(-30deg)]" />
        <div className="absolute [border:1px_solid_#b699f436] w-[180px] h-[180px] rounded-full top-[10px] left-[39px] [transform:rotate(45deg)]" />
        <div className="absolute top-[39px] left-[67px] w-[126px] h-[126px] rounded-[36%] [transform:rotate(-13deg)] grid place-items-center text-[#eee3ff] [background:radial-gradient(circle_at_28%_20%,#e2d6ff,#9673e4_40%,#584089_77%,#c4acfa)] shadow-[inset_-5px_-7px_15px_#eee1ff44,inset_3px_3px_10px_#fff8,0_0_45px_#a684e34d] [&_svg]:[transform:rotate(13deg)]">
          <Sparkles size={54} strokeWidth={1.2} />
        </div>
        <span className="absolute flex items-center gap-[8px] bg-[#3b334e] [border:1px_solid_#77618e70] text-[#d6c9ed] text-[9px] p-[10px_13px] rounded-[8px] shadow-[0_6px_20px_#17122244] top-[23px] right-0 [transform:rotate(7deg)]">
          <BookOpen size={15} /> План урока
        </span>
        <span className="absolute flex items-center gap-[8px] bg-[#3b334e] [border:1px_solid_#77618e70] text-[#d6c9ed] text-[9px] p-[10px_13px] rounded-[8px] shadow-[0_6px_20px_#17122244] bottom-[6px] left-[2px] [transform:rotate(-6deg)]">
          <Check size={15} /> Больше времени для важного
        </span>
        <span className="absolute text-[#cebbff] text-[27px] left-[7px] top-[13px]">✧</span>
        <span className="absolute text-[#cebbff] text-[17px] right-[12px] bottom-[44px]">✦</span>
      </div>
    </section>
  );
}
