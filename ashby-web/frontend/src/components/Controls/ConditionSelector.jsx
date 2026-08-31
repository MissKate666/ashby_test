import React, {useMemo, useState} from 'react';
import {useApp} from '../../context/AppContext';

// Every criterion is a ratio of some numerator (with an optional exponent) over
// density ρ. `numerator` holds the tokens shown above the fraction bar; the
// denominator is always ρ, rendered by <Formula> below the bar.
const conditionOptions=[
  ['stiffness',['E'],'Жёсткость тяг'],
  ['strength',['σ'],'Прочность тяг'],
  ['bending',['√E'],'Жёсткость балок'],
  ['plate_stiffness',['E',{sup:'1/3'}],'Жёсткость пластин'],
  ['beam_strength',['σ',{sup:'2/3'}],'Прочность балок'],
  ['column_stiffness',['E',{sup:'1/2'}],'Жёсткость колонн'],
];

const numeratorText = numerator => numerator.map(t => typeof t === 'string' ? t : `^(${t.sup})`).join('');
// Plain-text form of a formula, e.g. "E^(1/3)/ρ", used for search matching.
const formulaText = numerator => `${numeratorText(numerator)}/ρ`;

function Formula({numerator}) {
  return (
    <span className="inline-fraction">
      <span className="inline-fraction__num">
        {numerator.map((t, i) => typeof t === 'string'
          ? <React.Fragment key={i}>{t}</React.Fragment>
          : <sup key={i}>{t.sup}</sup>)}
      </span>
      <span className="inline-fraction__den">ρ</span>
    </span>
  );
}

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

  const set = (k, v) => setParams(p => ({...p, [k]: v, intercept: k === 'preference' ? null : p.intercept, intercepts: k === 'preference' ? {} : p.intercepts}));

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
