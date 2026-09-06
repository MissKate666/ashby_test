import React from 'react';
import {useApp} from '../../context/AppContext';
import {groupColor} from '../../lib/groupColor';

const EMPTY_SET = new Set();

export default function GroupLegend({condition, groups = []}) {
  const {hiddenGroupsByCondition, setHiddenGroupsFor, toggleGroup} = useApp();
  const hiddenGroups = hiddenGroupsByCondition[condition] ?? EMPTY_SET;
  const uniq = groups.filter(g => g.kind === 'group');

  return (
    // max-w keeps a long group name from growing this box wide enough to cover
    // the chart's zoom/settings toolbar (which sits at the same top offset but
    // a lower z-index); names wrap onto a second line instead of forcing width.
    <div className="absolute right-6 top-6 z-30 max-h-52 max-w-[11rem] overflow-auto rounded-[1.25rem] border border-[rgba(74,63,75,0.16)] bg-[rgba(240,217,228,0.88)] p-3 text-xs font-bold text-[rgb(22,19,31)] shadow-[0_18px_42px_rgba(74,63,75,0.16)] backdrop-blur md:max-h-64 md:max-w-[14rem]">
      {uniq.length > 1 && (
        <div className="mb-2 flex gap-2">
          <button
            type="button"
            className="touch-target flex-1 rounded-lg bg-[rgba(74,63,75,0.1)] px-2 py-1 text-xs font-black uppercase tracking-wide text-[rgb(74,63,75)] transition hover:bg-[rgba(74,63,75,0.2)]"
            onClick={() => setHiddenGroupsFor(condition, new Set())}
          >
            Показать все
          </button>
          <button
            type="button"
            className="touch-target flex-1 rounded-lg bg-[rgba(74,63,75,0.1)] px-2 py-1 text-xs font-black uppercase tracking-wide text-[rgb(74,63,75)] transition hover:bg-[rgba(74,63,75,0.2)]"
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
            className="touch-target flex w-full items-center gap-2 whitespace-normal break-words rounded-lg py-1 text-left transition hover:bg-[rgba(74,63,75,0.08)]"
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
