// Single source of truth for the group hue formula so the legend swatches,
// group/subgroup blob outlines, and material point fills can never drift
// apart the way two independently-maintained copies of this formula would.
export const groupHue = i => (318 + i * 47) % 360;
export const groupColor = i => `hsl(${groupHue(i)} 28% 56%)`;
