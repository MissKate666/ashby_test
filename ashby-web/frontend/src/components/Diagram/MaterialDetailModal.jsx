import React, {useEffect} from 'react';

export default function MaterialDetailModal({point, onClose}) {
  useEffect(() => {
    if (!point) return;
    const onKey = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [point, onClose]);

  if (!point) return null;

  const rows = [
    ['Группа', point.group],
    ['Подгруппа', point.subgroup],
    ['Плотность, кг/м³', point.density ?? point.x],
    ['Модуль Юнга, ГПа', point.youngs_modulus],
    ['Прочность, МПа', point.strength],
    ['Индекс эффективности (текущий критерий)', point.indexValue != null ? point.indexValue.toPrecision(4) : '—'],
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[rgba(22,19,31,0.55)] backdrop-blur-sm" onClick={onClose} />
      <div role="dialog" aria-modal="true" aria-label={`Материал: ${point.name}`} className="relative z-10 w-full max-w-md overflow-hidden rounded-[1.75rem] border border-[rgba(74,63,75,0.18)] bg-[rgb(240,217,228)] shadow-[0_30px_90px_rgba(22,19,31,0.35)]">
        <div className="flex items-center justify-between gap-3 border-b border-[rgba(74,63,75,0.14)] bg-[rgb(193,160,172)] px-6 py-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-[rgb(74,63,75)]">Материал</p>
            <h2 className="text-xl font-black text-[rgb(22,19,31)]">{point.name}</h2>
          </div>
          <button className="btn-secondary" onClick={onClose}>Закрыть ✕</button>
        </div>
        <dl className="grid gap-3 px-6 py-5">
          {rows.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between gap-3 border-b border-[rgba(74,63,75,0.1)] pb-2 last:border-b-0 last:pb-0">
              <dt className="text-sm font-bold text-[rgb(128,108,121)]">{label}</dt>
              <dd className="text-sm font-black text-[rgb(22,19,31)]">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
