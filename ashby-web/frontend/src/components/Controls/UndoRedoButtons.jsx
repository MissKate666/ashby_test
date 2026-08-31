import React from 'react';
import {useApp} from '../../context/AppContext';

function ChevronIcon({direction}) {
  const d = direction === 'left' ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6';
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

export default function UndoRedoButtons() {
  const {undo, redo, canUndo, canRedo} = useApp();
  return (
    <div className="flex items-center justify-center gap-2">
      <button
        type="button"
        className="btn-secondary flex items-center gap-1.5 disabled:cursor-not-allowed disabled:opacity-40"
        title="Отменить последнее действие"
        aria-label="Отменить последнее действие"
        disabled={!canUndo}
        onClick={undo}
      >
        <ChevronIcon direction="left" /> Назад
      </button>
      <button
        type="button"
        className="btn-secondary flex items-center gap-1.5 disabled:cursor-not-allowed disabled:opacity-40"
        title="Повторить отменённое действие"
        aria-label="Повторить отменённое действие"
        disabled={!canRedo}
        onClick={redo}
      >
        Вперёд <ChevronIcon direction="right" />
      </button>
    </div>
  );
}
