export const ui = {
  primary:
    'border-0 inline-flex items-center justify-center gap-[9px] rounded-[8px] text-[11px] font-[750] p-[13px_18px] min-h-[42px] bg-primary text-primary-foreground shadow-[0_4px_15px_#a38aee12] hover:bg-primary-hover',
  secondary:
    '[border:1px_solid_#40414e] inline-flex items-center justify-center gap-[9px] rounded-[8px] text-[11px] font-[750] p-[13px_18px] min-h-[42px] bg-[#30323f] text-[#d0ccdf] hover:bg-[#3b3c4b]',
  panel: 'bg-surface border border-line rounded-[14px] p-[25px] min-w-0 max-[760px]:p-[20px]',
  'icon-btn': 'bg-transparent border-0 p-[6px] grid place-items-center text-[#aaaabe]',
  back: 'bg-transparent border-0 p-0 text-[#aaa0c2] flex items-center gap-[8px] text-[11px] mb-[25px]',
  empty:
    'flex flex-col items-center text-center gap-[12px] p-[55px_20px] text-[#9d94b4] [&_h3]:m-0 [&_p]:m-0 [&_p]:text-[12px] [&_p]:max-w-[350px] [&>svg]:text-[#b5a1ff] [&>svg]:w-[31px] [&>svg]:h-[31px] [&_h3]:text-[#d8d0e9] [&_h3]:text-[17px]',
  difficulty:
    'bg-[#b59aef0b] [border-left:2px_solid_#a48cc9] p-[12px] text-[11px] leading-[1.8] text-[#c3b6dc] m-[15px_0]',
  brief:
    'bg-[#302a40] [border:1px_solid_#463a60] rounded-[10px] p-[18px] mb-[22px] text-[12px] text-[#c3b8d7] leading-[1.9] [&_h3]:m-[0_0_9px] [&_h3]:text-[#d6c5f7] [&_h3]:text-[13px] [&_p]:m-0',
  'page-heading':
    'flex items-center justify-between gap-[20px] mb-[30px] [&_p]:text-muted [&_p]:text-[12px] [&_p]:m-0 max-[760px]:items-start max-[760px]:flex-wrap max-[760px]:gap-[18px] max-[760px]:mb-[24px] max-[760px]:[&_p]:text-[11px]',
  eyebrow:
    'text-[9px] tracking-[1.9px] text-[#8f8ca7] font-extrabold mb-[12px] max-[760px]:text-[8px]',
  'section-toolbar':
    'flex items-center justify-between gap-[18px] mb-[22px] [&_h2>span]:text-[10px] [&_h2>span]:ml-[8px] [&_h2>span]:bg-[#30313e] [&_h2>span]:p-[3px_7px] [&_h2>span]:rounded-[5px] [&_h2>span]:text-[#aaa8bd] [&_p]:text-[10px] [&_p]:text-[#85899f] [&_p]:m-[7px_0_0] max-[760px]:flex-wrap max-[760px]:gap-[16px]',
  'lesson-actions': 'flex flex-wrap gap-[10px] mt-[21px] max-[760px]:[&>*]:flex-1',
  error:
    'flex items-center justify-between bg-[#49313b] text-[#ffd2df] p-[14px] [border:1px_solid_#74505b] rounded-[8px] mb-[20px] text-[12px] [&_button]:border-0 [&_button]:bg-transparent [&_button]:text-[inherit]',
} as const;
