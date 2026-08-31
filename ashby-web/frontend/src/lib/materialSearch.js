// Shared match test for the header's material search -- used both to highlight
// points on the chart (useDiagram.js) and to compute the "Found: X of Y" counter
// (MaterialSearch.jsx), so the two always agree on what counts as a match.
export function materialMatches(point, query) {
  const q = query.trim().toLowerCase();
  if (!q) return false;
  return [point.name, point.group, point.subgroup].some(v => String(v || '').toLowerCase().includes(q));
}
