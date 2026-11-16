import { ui } from '../components/ui/styles';
import { PreparationHero } from '../components/students/PreparationHero';
import { StudentCard } from '../components/students/StudentCard';
import { LayoutGrid, LoaderCircle, Plus, Search } from 'lucide-react';
import type { Workspace } from '../hooks/useWorkspace';

type Props = Pick<
  Workspace,
  'students' | 'query' | 'setQuery' | 'loading' | 'setModal' | 'openStudent'
>;
export function StudentsPage({ students, query, setQuery, loading, setModal, openStudent }: Props) {
  return (
    <>
      <div className={ui['page-heading']}>
        <div>
          <div className={ui['eyebrow']}>КАЖДЫЙ УЧЕНИК — СВОЯ ИСТОРИЯ</div>
          <h1>
            Мои ученики<span className="text-accent">.</span>
          </h1>
          <p>Всё, что нужно для следующего хорошего занятия.</p>
        </div>
        <button className={ui['primary']} onClick={() => setModal('student')}>
          <Plus size={18} />
          Добавить ученика
        </button>
      </div>
      <PreparationHero
        onPrepare={() => (students[0] ? openStudent(students[0]) : setModal('student'))}
      />
      <div className={ui['section-toolbar']}>
        <div>
          <h2>
            Все ученики <span>{students.length}</span>
          </h2>
          <p>Цели, занятия и прогресс — в одном месте</p>
        </div>
        <div className="flex items-center gap-[11px] max-[760px]:w-full">
          <label className="flex items-center gap-[9px] bg-[#22242f] [border:1px_solid_#343644] rounded-[8px] p-[0_12px] text-[#85889d] m-0 [&_input]:border-0 [&_input]:bg-transparent [&_input]:p-[11px_0] [&_input]:w-[170px] [&_input]:outline-none [&_input]:text-[10px] focus-within:border-accent max-[760px]:flex-1 max-[760px]:[&_input]:w-full">
            <Search size={17} />
            <input
              aria-label="Найти ученика"
              placeholder="Найти ученика…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <span className="bg-[#343041] text-[#c9b7ff] w-[35px] h-[35px] rounded-[7px] grid place-items-center">
            <LayoutGrid size={18} />
          </span>
        </div>
      </div>
      {loading ? (
        <div className={ui['empty']}>
          <LoaderCircle className="motion-safe:animate-spin" />
          Загружаем учеников…
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-[18px] min-[1500px]:grid-cols-4 max-[1150px]:grid-cols-2 max-[760px]:gap-[12px] max-[370px]:grid-cols-1">
          {students
            .filter((s) => (s.name + ' ' + s.grade).toLowerCase().includes(query.toLowerCase()))
            .map((s, i) => (
              <StudentCard key={s.id} student={s} index={i} onOpen={openStudent} />
            ))}
          <button
            className="bg-transparent [border:1px_dashed_#444152] rounded-[13px] min-h-[273px] flex flex-col items-center justify-center text-[#a49bb7] gap-[13px] hover:bg-[#a388ff09] hover:border-[#a38bc6] [&>span]:w-[45px] [&>span]:h-[45px] [&>span]:rounded-[14px] [&>span]:grid [&>span]:place-items-center [&>span]:bg-[#2c293a] [&>span]:text-[#bba2ed] [&_strong]:text-[12px] [&_p]:text-[10px] [&_p]:text-[#75798f] [&_p]:m-0 max-[760px]:min-h-[270px] max-[760px]:p-[10px] max-[760px]:text-center max-[760px]:[&_p]:text-[9px]"
            onClick={() => setModal('student')}
          >
            <span>
              <Plus size={25} />
            </span>
            <strong>Новый ученик</strong>
            <p>Начните новую историю обучения</p>
          </button>
        </div>
      )}
      {query &&
        !students.some((s) =>
          (s.name + ' ' + s.grade).toLowerCase().includes(query.toLowerCase()),
        ) && <p className="text-muted text-[12px]">По вашему запросу никого не найдено.</p>}
      <div className="flex gap-[9px] items-center text-[#7f8296] text-[9px] mt-[28px] leading-[1.7] max-[760px]:text-[9px]">
        <span className="inline-block w-[6px] h-[6px] bg-[#8dcab5] rounded-full shrink-0" />
        Материалы AI — черновики. Окончательное решение остаётся за вами.
      </div>
    </>
  );
}
