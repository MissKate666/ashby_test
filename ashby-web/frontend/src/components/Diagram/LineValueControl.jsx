import React, {useEffect, useState} from 'react';
import {useApp} from '../../context/AppContext';

const isSet = v => v !== '' && v !== null && v !== undefined;

function formatValue(value) {
  if (value === null || value === undefined || !isFinite(value)) return '';
  return Number(value.toPrecision(6)).toString();
}

// Computed directly from each point's own x (density) and y (whichever property
// the current criterion uses) via the criterion's slope, exactly mirroring the
// backend's own formula (see diagram.py's analyze()) -- not read from a fixed
// per-criterion CSV column, which doesn't exist for every criterion and (checked
// against the dataset) doesn't reliably match this formula for the ones that do.
function computeRange(data, bounds) {
  const slope = data?.condition_line?.slope;
  if (!slope || !data?.points?.length) return null;
  const values = data.points
    .filter(p => {
      if (isSet(bounds.x_min) && p.x < Number(bounds.x_min)) return false;
      if (isSet(bounds.x_max) && p.x > Number(bounds.x_max)) return false;
      if (isSet(bounds.y_min) && p.y < Number(bounds.y_min)) return false;
      if (isSet(bounds.y_max) && p.y > Number(bounds.y_max)) return false;
      return true;
    })
    .map(p => 10 ** ((Math.log10(p.y) - slope * Math.log10(p.x)) / slope))
    .filter(v => typeof v === 'number' && isFinite(v) && v > 0);
  if (!values.length) return null;
  return [Math.min(...values), Math.max(...values)];
}

const EMPTY_BOUNDS = {};

export default function LineValueControl({condition, data}) {
  const {params, setParams, axisBoundsByCondition} = useApp();
  const line = data?.condition_line;
  const currentValue = line && line.slope ? 10 ** (line.intercept / line.slope) : null;
  const manualActive = isSet(params.intercepts?.[condition]) || (params.syncLines && isSet(params.intercept));
  const range = computeRange(data, axisBoundsByCondition[condition] ?? EMPTY_BOUNDS);
  const disabled = !line || !range;

  const [text, setText] = useState('');
  const [warning, setWarning] = useState('');

  useEffect(() => {
    if (disabled) { setText(''); return; }
    setText(manualActive ? formatValue(currentValue) : '');
  }, [condition, manualActive, currentValue, disabled]);

  // Dragging the line on the chart moves it live via direct D3/DOM updates (see
  // useDiagram.js), bypassing React state so it doesn't wait on a setParams -> API
  // round-trip per frame. This registers a hook so the same live value reaches this
  // field on every drag tick, instead of only once the drag ends and params commit.
  useEffect(() => {
    window.__ashbyLiveIndexValue = window.__ashbyLiveIndexValue || {};
    window.__ashbyLiveIndexValue[condition] = (value) => setText(formatValue(value));
    return () => {
      if (window.__ashbyLiveIndexValue) delete window.__ashbyLiveIndexValue[condition];
    };
  }, [condition]);

  const resetValue = () => {
    setWarning('');
    setParams(p => {
      if (p.syncLines) return {...p, intercept: null, intercepts: {}};
      const intercepts = {...(p.intercepts || {})};
      delete intercepts[condition];
      return {...p, intercepts};
    });
  };

  const revertText = () => setText(manualActive ? formatValue(currentValue) : '');

  const commit = () => {
    const raw = text.trim().replace(',', '.');
    if (!raw) {
      resetValue();
      return;
    }
    const value = Number(raw);
    if (!Number.isFinite(value)) {
      revertText();
      return;
    }
    if (range && (value < range[0] || value > range[1])) {
      setWarning(`Вне диапазона: ${formatValue(range[0])} – ${formatValue(range[1])}`);
      revertText();
      return;
    }
    setWarning('');
    window.__ashbySetValue?.[condition]?.(value);
  };

  const tooltip = disabled
    ? 'Нет данных для расчёта диапазона'
    : `Допустимый диапазон: ${formatValue(range[0])} — ${formatValue(range[1])}`;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-xs font-black text-[rgb(22,19,31)]">
        <input
          className="w-full touch-target rounded-xl border border-[rgba(74,63,75,0.24)] bg-white/70 px-2 py-1 text-xs font-bold text-[rgb(22,19,31)] shadow-sm transition focus:outline-none focus:ring-2 focus:ring-[rgb(74,63,75)] disabled:opacity-50"
          placeholder={disabled ? 'нет данных' : 'Авто'}
          title={tooltip}
          value={text}
          disabled={disabled}
          onChange={e => setText(e.target.value)}
          onBlur={commit}
          onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur(); }}
        />
        <button type="button" className="btn-secondary px-2 py-1 text-[10px]" disabled={disabled || !manualActive} onClick={resetValue}>Сброс</button>
      </div>
      {warning && <span className="rounded-xl bg-[rgba(74,63,75,0.1)] px-2 py-1 text-[11px] font-bold text-[rgb(180,30,30)]">{warning}</span>}
    </div>
  );
}
