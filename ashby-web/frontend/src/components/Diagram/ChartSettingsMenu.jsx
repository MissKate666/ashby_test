import React, {useEffect, useRef, useState} from 'react';
import {useApp} from '../../context/AppContext';
import LineValueControl from './LineValueControl';
import AxisLimits from '../Controls/AxisLimits';

export default function ChartSettingsMenu({condition, data}) {
  const {params, toggleSyncLines} = useApp();
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onDocClick = e => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = e => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onDocClick);
    window.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div className="pointer-events-auto relative" ref={rootRef}>
      <button
        type="button"
        className="btn-secondary"
        title="Настройки графика"
        aria-label="Настройки графика"
        aria-expanded={open}
        onClick={() => setOpen(v => !v)}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      </button>
      {open && (
        <div className="absolute left-0 top-full z-40 mt-2 w-72 rounded-[1.25rem] border border-[rgba(74,63,75,0.16)] bg-[rgb(240,217,228)] p-4 shadow-[0_18px_42px_rgba(74,63,75,0.22)]">
          <div className="mb-2 flex items-center justify-between gap-2">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-[rgb(74,63,75)]">Индекс эффективности</p>
            <button
              type="button"
              className={`sync-toggle-btn ${params.syncLines ? 'sync-toggle-btn--active' : ''}`}
              title="Двигать линии синхронно на всех графиках"
              aria-label="Двигать линии синхронно на всех графиках"
              aria-pressed={params.syncLines}
              onClick={toggleSyncLines}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round">
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
          </div>
          <LineValueControl condition={condition} data={data} />
          <p className="mb-2 mt-4 text-xs font-black uppercase tracking-[0.2em] text-[rgb(74,63,75)]">Границы осей</p>
          <AxisLimits condition={condition} />
        </div>
      )}
    </div>
  );
}
