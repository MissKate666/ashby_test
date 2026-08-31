import React from 'react';
import {useApp} from '../../context/AppContext';

const groupColor = i => `hsl(${(318 + i * 47) % 360} 28% 56%)`;
const EMPTY_SET = new Set();

export default function GroupLegend({condition, groups = []}) {
  const {hiddenGroupsByCondition, setHiddenGroupsFor, toggleGroup} = useApp();
  const hiddenGroups = hiddenGroupsByCondition[condition] ?? EMPTY_SET;
  const uniq = groups.filter(g => g.kind === 'group');

  return (
    <div className="absolute right-6 top-6 z-30 max-h-52 overflow-auto rounded-[1.25rem] border border-[rgba(74,63,75,0.16)] bg-[rgba(240,217,228,0.88)] p-3 text-xs font-bold text-[rgb(22,19,31)] shadow-[0_18px_42px_rgba(74,63,75,0.16)] backdrop-blur md:max-h-64">
      {uniq.length > 1 && (
        <div className="mb-2 flex gap-2">
          <button
            type="button"
            className="rounded-lg bg-[rgba(74,63,75,0.1)] px-2 py-1 text-[10px] font-black uppercase tracking-wide text-[rgb(74,63,75)] transition hover:bg-[rgba(74,63,75,0.2)]"
            onClick={() => setHiddenGroupsFor(condition, new Set())}
          >
            Показать все
          </button>
          <button
            type="button"
            className="rounded-lg bg-[rgba(74,63,75,0.1)] px-2 py-1 text-[10px] font-black uppercase tracking-wide text-[rgb(74,63,75)] transition hover:bg-[rgba(74,63,75,0.2)]"
            onClick={() => setHiddenGroupsFor(condition, new Set(uniq.map(g => g.name)))}
          >
            Скрыть все
          </button>
        </div>
      )}
      {uniq.map((g, i) => {
        const hidden = hiddenGroups.has(g.name);
        return (
          <button
            key={g.id}
            type="button"
            title={hidden ? `Показать группу «${g.name}»` : `Скрыть группу «${g.name}»`}
            className="flex w-full items-center gap-2 whitespace-nowrap rounded-lg py-1 text-left transition hover:bg-[rgba(74,63,75,0.08)]"
            style={{opacity: hidden ? 0.4 : 1}}
            onClick={() => toggleGroup(condition, g.name)}
          >
            <span
              className="h-3 w-3 shrink-0 rounded-full border border-[rgba(22,19,31,0.25)]"
              style={{background: hidden ? 'rgb(160,160,160)' : groupColor(i), opacity: hidden ? 0.6 : 0.78}}
            />
            <span style={{textDecoration: hidden ? 'line-through' : 'none'}}>{g.name}</span>
          </button>
        );
      })}
    </div>
  );
}
