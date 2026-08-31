import React from 'react';

// Every criterion is a ratio of some numerator (with an optional exponent) over
// density ρ. `numerator` holds the tokens shown above the fraction bar; the
// denominator is always ρ, rendered by <Formula> below the bar. This is the
// single source of truth for criterion formulas -- shared by the criteria
// checklist (ConditionSelector) and each chart's title chip (AshbyDiagram),
// so both render the exact same fraction.
export const CONDITION_OPTIONS = [
  ['stiffness', ['E'], 'Жёсткость тяг'],
  ['strength', ['σ'], 'Прочность тяг'],
  ['bending', ['√E'], 'Жёсткость балок'],
  ['plate_stiffness', ['E', {sup: '1/3'}], 'Жёсткость пластин'],
  ['beam_strength', ['σ', {sup: '2/3'}], 'Прочность балок'],
  ['column_stiffness', ['E', {sup: '1/2'}], 'Жёсткость колонн'],
];

export const CONDITION_MAP = Object.fromEntries(
  CONDITION_OPTIONS.map(([value, numerator, description]) => [value, {numerator, description}])
);

export const numeratorText = numerator => numerator.map(t => typeof t === 'string' ? t : `^(${t.sup})`).join('');
// Plain-text form of a formula, e.g. "E^(1/3)/ρ", used for search matching.
export const formulaText = numerator => `${numeratorText(numerator)}/ρ`;

export function Formula({numerator}) {
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

// Renders a criterion's formula + description the same way everywhere
// (chart title chips, the criteria checklist); falls back to plain text
// for conditions with no formula (e.g. "none").
export function CriterionLabel({condition, fallback}) {
  const entry = CONDITION_MAP[condition];
  if (!entry) return <>{fallback}</>;
  return <><Formula numerator={entry.numerator} /> — {entry.description}</>;
}
