import React, {useState} from 'react';
import {exportFile} from '../../services/api';
import {useApp} from '../../context/AppContext';

// Only the primitive fields the backend's export endpoints actually accept --
// spreading the whole `params` object (as this used to do) sent `intercepts`
// (an object) and `conditions` (an array) straight into the query string,
// which serialize to garbage like "[object Object]".
function buildExportParams(params, bounds) {
  const intercept = params.syncLines
    ? params.intercepts?.[params.condition] ?? params.intercept
    : params.intercepts?.[params.condition] ?? null;
  const raw = {
    condition: params.condition,
    preference: params.preference,
    intercept,
    x_min: bounds.x_min, x_max: bounds.x_max, y_min: bounds.y_min, y_max: bounds.y_max,
  };
  return Object.fromEntries(Object.entries(raw).filter(([, v]) => v !== undefined && v !== null && v !== ''));
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function ExportButton({suitableCount, multiChart}) {
  const {params, axisBoundsByCondition} = useApp();
  const bounds = axisBoundsByCondition[params.condition] || {};
  const [pending, setPending] = useState(null);
  const [error, setError] = useState('');
  const disabled = suitableCount === 0;

  const run = async type => {
    if (pending) return; // guards against a double-click firing two downloads
    setPending(type);
    setError('');
    try {
      const {blob, filename} = await exportFile(type, buildExportParams(params, bounds));
      downloadBlob(blob, filename);
    } catch {
      setError('Не удалось экспортировать таблицу. Попробуйте ещё раз.');
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          className="btn-secondary text-center disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled || pending !== null}
          onClick={() => run('csv')}
        >
          {pending === 'csv' ? 'Экспорт…' : 'CSV'}
        </button>
        <button
          type="button"
          className="btn-primary text-center disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled || pending !== null}
          onClick={() => run('excel')}
        >
          {pending === 'excel' ? 'Экспорт…' : 'Excel'}
        </button>
      </div>
      {multiChart && (
        <span className="text-[11px] font-bold text-[rgb(74,63,75)]">
          Экспортируется первая выбранная диаграмма: {params.condition}
        </span>
      )}
      {disabled && <span className="text-[11px] font-bold text-[rgb(74,63,75)]">Нет подходящих материалов для экспорта</span>}
      {error && <span className="text-[11px] font-bold text-[rgb(180,30,30)]">{error}</span>}
    </div>
  );
}
