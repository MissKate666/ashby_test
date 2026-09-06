import React, {useEffect, useMemo, useRef, useState} from 'react';
import {useApp} from '../../context/AppContext';
import {materialMatches} from '../../lib/materialSearch';

const DEBOUNCE_MS = 250;

export default function MaterialSearch({points}) {
  const {searchQuery, setSearchQuery} = useApp();
  const inputRef = useRef(null);
  const timeoutRef = useRef(null);
  const [text, setText] = useState(searchQuery);

  // `text` updates on every keystroke so the input feels instant, but the
  // shared `searchQuery` (a dependency of useDiagram's render effect, which
  // rebuilds the entire SVG on every open chart) only updates after a short
  // pause, so typing doesn't rebuild the diagram once per character.
  const onChange = e => {
    const value = e.target.value;
    setText(value);
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setSearchQuery(value), DEBOUNCE_MS);
  };

  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  const matches = useMemo(
    () => searchQuery.trim() ? (points || []).filter(p => materialMatches(p, searchQuery)) : [],
    [points, searchQuery]
  );

  const total = points?.length ?? 0;
  const isActive = text.trim().length > 0;
  const pending = text !== searchQuery;

  let status = null;
  if (isActive) {
    if (pending) status = 'Поиск…';
    else if (matches.length === 0) status = 'Ничего не найдено';
    else if (matches.length === 1) status = `Найдено: ${matches[0].name}`;
    else status = `Найдено: ${matches.length} из ${total} материалов`;
  }

  const clear = () => {
    clearTimeout(timeoutRef.current);
    setText('');
    setSearchQuery('');
    inputRef.current?.focus();
  };

  const onKeyDown = e => {
    if (e.key === 'Escape') clear();
  };

  return (
    <div className="mt-3 max-w-md">
      <div className="relative">
        <svg className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[rgb(74,63,75)]" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder="Поиск материала..."
          aria-label="Поиск материала"
          className="w-full touch-target rounded-2xl border border-[rgba(74,63,75,0.24)] bg-[rgba(240,217,228,0.86)] py-2 pl-10 pr-9 text-sm font-bold text-[rgb(22,19,31)] shadow-[0_10px_22px_rgba(74,63,75,0.14)] transition focus:outline-none focus:ring-2 focus:ring-[rgb(74,63,75)]"
        />
        {isActive && (
          <button
            type="button"
            onClick={clear}
            title="Очистить поиск"
            aria-label="Очистить поиск"
            className="absolute right-2 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full text-[rgb(74,63,75)] hover:bg-[rgba(74,63,75,0.12)]"
          >
            ✕
          </button>
        )}
      </div>
      {status && (
        <p className="mt-1.5 px-1 text-xs font-black text-[rgb(74,63,75)]">{status}</p>
      )}
    </div>
  );
}
