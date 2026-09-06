import React, {useEffect, useState} from 'react';
import {useApp} from '../../context/AppContext';

const EMPTY_BOUNDS = {};
const FIELDS = [['x_min', 'X min'], ['x_max', 'X max'], ['y_min', 'Y min'], ['y_max', 'Y max']];

const toText = v => (v === undefined || v === null ? '' : String(v));
const localFrom = bounds => ({
  x_min: toText(bounds.x_min), x_max: toText(bounds.x_max),
  y_min: toText(bounds.y_min), y_max: toText(bounds.y_max),
});

export default function AxisLimits({condition}) {
  const {axisBoundsByCondition, setAxisBoundsFor} = useApp();
  const bounds = axisBoundsByCondition[condition] ?? EMPTY_BOUNDS;
  const [local, setLocal] = useState(() => localFrom(bounds));
  const [errors, setErrors] = useState({});

  // Commits happen on blur/Enter (see commit() below), not on every keystroke --
  // so re-sync the visible text only when the committed value changes from
  // elsewhere (switching chart, undo/redo), mirroring LineValueControl's pattern.
  useEffect(() => {
    setLocal(localFrom(bounds));
    setErrors({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [condition, bounds.x_min, bounds.x_max, bounds.y_min, bounds.y_max]);

  const commit = key => {
    const raw = local[key].trim().replace(',', '.');
    if (!raw) {
      setErrors(e => ({...e, [key]: null}));
      if (bounds[key] !== undefined && bounds[key] !== null) setAxisBoundsFor(condition, {[key]: null});
      return;
    }
    const value = Number(raw);
    if (!Number.isFinite(value) || value <= 0) {
      setErrors(e => ({...e, [key]: 'Введите положительное число'}));
      return;
    }
    const next = {...bounds, [key]: value};
    if (next.x_min != null && next.x_max != null && Number(next.x_min) > Number(next.x_max)) {
      setErrors(e => ({...e, [key]: 'X min должен быть ≤ X max'}));
      return;
    }
    if (next.y_min != null && next.y_max != null && Number(next.y_min) > Number(next.y_max)) {
      setErrors(e => ({...e, [key]: 'Y min должен быть ≤ Y max'}));
      return;
    }
    setErrors(e => ({...e, [key]: null}));
    if (Number(bounds[key]) !== value) setAxisBoundsFor(condition, {[key]: value});
  };

  return (
    <div className="grid grid-cols-2 gap-3">
      {FIELDS.map(([k, l]) => (
        <label className="panel-label" key={k}>
          {l}
          <input
            type="text"
            inputMode="decimal"
            className="panel-input mt-1"
            style={errors[k] ? {boxShadow: '0 0 0 2px rgb(180,30,30)'} : undefined}
            placeholder="без ограничения"
            value={local[k]}
            onChange={e => setLocal(l0 => ({...l0, [k]: e.target.value}))}
            onBlur={() => commit(k)}
            onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur(); }}
          />
          {errors[k] && <span className="mt-1 block text-[11px] font-bold text-[rgb(180,30,30)]">{errors[k]}</span>}
        </label>
      ))}
    </div>
  );
}
