// The sidebar's width (layout look §3.2): 245 px by default, resizable from 220 to 480 px. A stored
// width that is missing, broken or out of range comes back inside the limits.
export const SIDEBAR_WIDTH = { min: 220, max: 480, initial: 245 } as const;

export function sidebarWidth(stored: unknown): number {
  const width = Number(stored);
  if (stored === undefined || stored === null || !Number.isFinite(width))
    return SIDEBAR_WIDTH.initial;
  return Math.min(SIDEBAR_WIDTH.max, Math.max(SIDEBAR_WIDTH.min, Math.round(width)));
}
