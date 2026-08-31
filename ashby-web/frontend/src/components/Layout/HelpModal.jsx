import React, {useEffect} from 'react';
import {CONDITION_OPTIONS, Formula} from '../../lib/conditionFormulas';

const details = {
  stiffness: {
    area: 'Тяги и стержни, растянутые или сжатые вдоль оси (тросы, стойки, спицы) — где важна минимальная деформация (растяжение/сжатие) при минимальной массе.',
    meaning: 'Чем выше значение, тем более жёсткий материал получается на единицу массы — лучше для лёгких жёстких тяг. Низкое значение — материал даёт меньше жёсткости на ту же массу.',
  },
  strength: {
    area: 'Тяги и стержни, растянутые или сжатые вдоль оси — где важно не превысить предел прочности при минимальной массе.',
    meaning: 'Чем выше значение, тем больше прочности на единицу массы — лучше для лёгких прочных тяг. Низкое значение — материал слабее на ту же массу.',
  },
  bending: {
    area: 'Балки, работающие на изгиб (рамы, крылья, велосипедные рамы) — где важна изгибная жёсткость при минимальном весе.',
    meaning: 'Чем выше значение, тем более жёсткая на изгиб балка получается на единицу массы. Низкое значение — балка прогибается сильнее при той же массе.',
  },
  plate_stiffness: {
    area: 'Плоские панели и пластины, работающие на изгиб (обшивка, панели) — где важна изгибная жёсткость панели при минимальном весе.',
    meaning: 'Чем выше значение, тем более жёсткая на изгиб пластина получается на единицу массы. Низкое значение — пластина прогибается сильнее при той же массе.',
  },
  beam_strength: {
    area: 'Балки, работающие на изгиб — где важно не разрушиться (не превысить предел прочности) при минимальном весе.',
    meaning: 'Чем выше значение, тем прочнее на изгиб балка получается на единицу массы. Низкое значение — балка слабее на ту же массу.',
  },
  column_stiffness: {
    area: 'Стойки и колонны, сжатые вдоль оси — где важна устойчивость к продольному изгибу (потере устойчивости) при минимальном весе. Формула та же, что и для жёсткости балок (√E/ρ) — это один и тот же классический индекс Эшби, применяемый в двух разных задачах: изгиб балки и устойчивость колонны.',
    meaning: 'Чем выше значение, тем устойчивее к продольному изгибу колонна на единицу массы. Низкое значение — колонна теряет устойчивость легче при той же массе.',
  },
};

export default function HelpModal({open, onClose}) {
  useEffect(() => {
    if (!open) return;
    const onKey = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[rgba(22,19,31,0.55)] backdrop-blur-sm" onClick={onClose} />
      <div role="dialog" aria-modal="true" aria-label="Справка по критериям эффективности" className="relative z-10 flex max-h-[85vh] w-full max-w-3xl flex-col overflow-hidden rounded-[1.75rem] border border-[rgba(74,63,75,0.18)] bg-[rgb(240,217,228)] shadow-[0_30px_90px_rgba(22,19,31,0.35)]">
        <div className="flex items-center justify-between gap-3 border-b border-[rgba(74,63,75,0.14)] bg-[rgb(193,160,172)] px-6 py-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-[rgb(74,63,75)]">Справка</p>
            <h2 className="text-xl font-black text-[rgb(22,19,31)]">Критерии эффективности</h2>
          </div>
          <button className="btn-secondary" onClick={onClose}>Закрыть ✕</button>
        </div>
        <div className="min-h-0 flex-1 overflow-auto px-6 py-5">
          <div className="grid gap-4">
            {CONDITION_OPTIONS.map(([value, numerator, description]) => (
              <div key={value} className="rounded-[1.25rem] border border-[rgba(74,63,75,0.16)] bg-[rgba(240,217,228,0.6)] p-4 shadow-[inset_0_1px_0_rgba(240,217,228,0.72)]">
                <div className="mb-2 flex items-center gap-3">
                  <span className="text-2xl font-black text-[rgb(22,19,31)]"><Formula numerator={numerator} /></span>
                  <span className="text-base font-black text-[rgb(22,19,31)]">— {description}</span>
                </div>
                <dl className="grid gap-1.5 text-sm">
                  <div className="grid grid-cols-[8rem_1fr] gap-2">
                    <dt className="font-black uppercase tracking-[0.1em] text-[rgb(128,108,121)]">Применение</dt>
                    <dd className="font-semibold text-[rgb(22,19,31)]">{details[value].area}</dd>
                  </div>
                  <div className="grid grid-cols-[8rem_1fr] gap-2">
                    <dt className="font-black uppercase tracking-[0.1em] text-[rgb(128,108,121)]">Значение</dt>
                    <dd className="font-semibold text-[rgb(22,19,31)]">{details[value].meaning}</dd>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
