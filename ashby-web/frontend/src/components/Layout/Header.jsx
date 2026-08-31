import React, {useState} from 'react';
import HelpModal from './HelpModal';
import MaterialSearch from './MaterialSearch';

export default function Header({onMenu, summary}){
  const [helpOpen, setHelpOpen] = useState(false);
  return (
    <header className="relative overflow-hidden rounded-[2rem] border border-[rgba(74,63,75,0.18)] bg-[rgb(193,160,172)] p-4 shadow-[0_24px_70px_rgba(74,63,75,0.18)] md:p-6">
      <div className="absolute -right-16 -top-24 h-48 w-48 rounded-full bg-[rgb(240,217,228)] opacity-70"/>
      <div className="absolute bottom-0 right-20 h-24 w-24 rounded-full bg-[rgb(128,108,121)] opacity-25"/>
      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="mb-2 inline-flex rounded-full bg-[rgba(240,217,228,0.72)] px-3 py-1 text-xs font-black uppercase tracking-[0.28em] text-[rgb(74,63,75)]">Ashby atlas</p>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-black leading-tight text-[rgb(22,19,31)] md:text-4xl">Интерактивная диаграмма Эшби</h1>
            <button
              type="button"
              onClick={() => setHelpOpen(true)}
              title="Справка по критериям эффективности"
              aria-label="Справка по критериям эффективности"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[rgba(74,63,75,0.24)] bg-[rgba(240,217,228,0.86)] text-base font-black text-[rgb(74,63,75)] shadow-[0_10px_22px_rgba(74,63,75,0.14)] transition hover:bg-[rgb(240,217,228)] hover:text-[rgb(22,19,31)]"
            >
              ?
            </button>
          </div>
          <p className="mt-2 max-w-2xl text-sm font-semibold text-[rgb(74,63,75)] md:text-base">Эстетичный подбор материалов с мягкой палитрой, выразительными акцентами и чистой научной визуализацией.</p>
          <MaterialSearch points={summary?.points} />
        </div>
        <button onClick={onMenu} className="btn-secondary lg:hidden">☰</button>
      </div>
      <HelpModal open={helpOpen} onClose={() => setHelpOpen(false)} />
    </header>
  );
}
