import React, {useMemo, useState} from 'react';
import {useApp} from '../../context/AppContext';
import {CONDITION_OPTIONS as conditionOptions, formulaText, Formula} from '../../lib/conditionFormulas';

export default function ConditionSelector() {
  const {params, setParams} = useApp();
  const [query, setQuery] = useState('');
  const selected = params.conditions?.length ? params.conditions : [params.condition].filter(Boolean);
  const normalizedQuery = query.trim().toLocaleLowerCase('ru');
  const visibleOptions = useMemo(
    () => conditionOptions
      .filter(([, numerator, description]) => `${formulaText(numerator)} — ${description}`.toLocaleLowerCase('ru').includes(normalizedQuery))
      .sort(([av,,ad], [bv,,bd]) => {
        const selectedDelta = Number(selected.includes(bv)) - Number(selected.includes(av));
        return selectedDelta || ad.localeCompare(bd, 'ru');
      }),
    [normalizedQuery, selected]
  );

  const toggle = condition => setParams(p => {
    const current = p.conditions?.length ? p.conditions : [p.condition].filter(Boolean);
    const next = current.includes(condition) ? current.filter(v => v !== condition) : [...current, condition];
    const conditions = next.length ? next : [condition];
    return {...p, conditions, condition: conditions[0], intercept: null, intercepts: {}};
  });

  const set = (k, v) => setParams(p => {
    if (k !== 'preference') return {...p, [k]: v};
    // Flipping High/Low silently discarded any manually dragged line position --
    // ask first so the user isn't surprised by losing a custom placement.
    const hasCustomLine = Object.keys(p.intercepts || {}).length > 0 || (p.syncLines && p.intercept != null);
    if (hasCustomLine && !window.confirm('Изменение "Подходит" сбросит вручную заданное положение линии критерия. Продолжить?')) {
      return p;
    }
    return {...p, preference: v, intercept: null, intercepts: {}};
  });

  return (
    <div className="grid gap-3">
      <div>
        <p className="panel-label mb-2">Критерии эффективности</p>
        <input className="panel-input mb-2" placeholder="Поиск критерия" value={query} onChange={e => setQuery(e.target.value)} />
        <div className="max-h-52 overflow-y-auto pr-1">
          <div className="grid gap-2">
            {visibleOptions.map(([value, numerator, description]) => (
              <label key={value} className="flex items-center gap-2 rounded-xl bg-[rgba(240,217,228,0.5)] px-3 py-2 text-sm font-bold text-[rgb(22,19,31)]">
                <input type="checkbox" checked={selected.includes(value)} onChange={() => toggle(value)} />
                <span className="whitespace-nowrap text-base"><Formula numerator={numerator} /></span>
                <span className="text-[rgb(74,63,75)]">— {description}</span>
              </label>
            ))}
            {!visibleOptions.length && (
              <p className="rounded-xl bg-[rgba(240,217,228,0.5)] px-3 py-2 text-sm font-bold text-[rgb(74,63,75)]">Ничего не найдено</p>
            )}
          </div>
        </div>
      </div>
      <label className="panel-label">
        Подходит
        <select className="panel-input mt-1" value={params.preference} onChange={e => set('preference', e.target.value)}>
          <option value="high">Высокое значение</option>
          <option value="low">Низкое значение</option>
        </select>
      </label>
    </div>
  );
}
