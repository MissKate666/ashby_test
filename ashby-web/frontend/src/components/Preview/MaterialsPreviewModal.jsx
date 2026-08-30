import React, {useEffect, useMemo, useState} from 'react';
import {useApp} from '../../context/AppContext';

const columns = [
  ['name', 'Материал'],
  ['group', 'Группа'],
  ['subgroup', 'Подгруппа'],
  ['density', 'Плотность, кг/м³'],
  ['youngs_modulus', 'Модуль Юнга, ГПа'],
  ['strength', 'Прочность, МПа'],
];

export default function MaterialsPreviewModal({open, onClose, points}) {
  const {hiddenGroups} = useApp();
  const [sortKey, setSortKey] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  useEffect(() => {
    if (!open) return;
    const onKey = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const rows = useMemo(() => {
    // Hiding a group in the legend is a display filter on the chart; the preview
    // table is another view of the same materials, so it must respect the same
    // hidden groups instead of listing materials the user just hid.
    const list = (points || []).filter(p => p.is_suitable && !hiddenGroups.has(p.group));
    list.sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey];
      const cmp = typeof av === 'number' && typeof bv === 'number'
        ? av - bv
        : String(av ?? '').localeCompare(String(bv ?? ''), 'ru');
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return list;
  }, [points, hiddenGroups, sortKey, sortDir]);

  if (!open) return null;

  const toggleSort = key => {
    if (key === sortKey) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[rgba(22,19,31,0.55)] backdrop-blur-sm" onClick={onClose} />
      <div role="dialog" aria-modal="true" aria-label="Предпросмотр подходящих материалов" className="relative z-10 flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-[1.75rem] border border-[rgba(74,63,75,0.18)] bg-[rgb(240,217,228)] shadow-[0_30px_90px_rgba(22,19,31,0.35)]">
        <div className="flex items-center justify-between gap-3 border-b border-[rgba(74,63,75,0.14)] bg-[rgb(193,160,172)] px-6 py-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-[rgb(74,63,75)]">Предпросмотр</p>
            <h2 className="text-xl font-black text-[rgb(22,19,31)]">Подходящие материалы: {rows.length}</h2>
          </div>
          <button className="btn-secondary" onClick={onClose}>Закрыть ✕</button>
        </div>
        <div className="min-h-0 flex-1 overflow-auto px-2 py-2">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 bg-[rgb(240,217,228)]">
              <tr>
                {columns.map(([key, label]) => (
                  <th
                    key={key}
                    className="cursor-pointer select-none whitespace-nowrap px-4 py-3 font-black text-[rgb(74,63,75)]"
                    onClick={() => toggleSort(key)}
                    aria-sort={sortKey === key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                  >
                    {label}{sortKey === key ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.name} className="border-t border-[rgba(74,63,75,0.1)] odd:bg-[rgba(193,160,172,0.14)]">
                  <td className="px-4 py-2 font-bold text-[rgb(22,19,31)]">{r.name}</td>
                  <td className="px-4 py-2">{r.group}</td>
                  <td className="px-4 py-2">{r.subgroup}</td>
                  <td className="px-4 py-2">{r.density}</td>
                  <td className="px-4 py-2">{r.youngs_modulus}</td>
                  <td className="px-4 py-2">{r.strength}</td>
                </tr>
              ))}
              {!rows.length && (
                <tr><td colSpan={columns.length} className="px-4 py-8 text-center font-bold text-[rgb(128,108,121)]">Нет подходящих материалов</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
