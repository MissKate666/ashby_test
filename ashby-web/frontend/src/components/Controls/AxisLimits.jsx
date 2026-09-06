import React from 'react';
import {useApp} from '../../context/AppContext';

const EMPTY_BOUNDS = {};
const names = [['x_min', 'X min'], ['x_max', 'X max'], ['y_min', 'Y min'], ['y_max', 'Y max']];

export default function AxisLimits({condition}) {
  const {axisBoundsByCondition, setAxisBoundsFor} = useApp();
  const bounds = axisBoundsByCondition[condition] ?? EMPTY_BOUNDS;
  return (
    <div className="grid grid-cols-2 gap-3">
      {names.map(([k, l]) => (
        <label className="panel-label" key={k}>
          {l}
          <input
            inputMode="decimal"
            className="panel-input mt-1"
            placeholder="без ограничения"
            value={bounds[k] ?? ''}
            onChange={e => setAxisBoundsFor(condition, {[k]: e.target.value})}
          />
        </label>
      ))}
    </div>
  );
}
