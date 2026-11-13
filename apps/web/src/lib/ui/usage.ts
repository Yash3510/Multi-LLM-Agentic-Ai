// The usage page's numbers and heat map (chat-composer look §9.12, F101), as the running app
// draws them: compact counts, durations, the level of each day, its palette and the month labels.
import type { UsageDay } from '$lib/data';

export type HeatMode = 'daily' | 'weekly' | 'cumulative';

/** 50200 → "50.2k". */
export const compact = (value: number) =>
  new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 })
    .format(value)
    .toLowerCase();

/** Seconds as "1d 1h", "1h 1m" or "2m". */
export function duration(seconds: number): string {
  const days = Math.floor(seconds / 86_400);
  const hours = Math.floor((seconds % 86_400) / 3_600);
  const minutes = Math.floor((seconds % 3_600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

/** 0 for none, then under 5, 5 to 9, 10 to 19, and 20 or more messages. */
export function intensity(day: UsageDay): 0 | 1 | 2 | 3 | 4 {
  const count = day.messages;
  if (count >= 20) return 4;
  if (count >= 10) return 3;
  if (count >= 5) return 2;
  return count > 0 ? 1 : 0;
}

const HUES = [
  'green',
  'blue',
  'purple',
  'orange',
  'rose',
  'yellow',
  'cyan',
  'red',
  'neutral',
] as const;
export type Hue = (typeof HUES)[number];

/** The palette of a model, by the first letter of its id ("a" the first); none takes the first. */
export function paletteFor(modelId: string | undefined): Hue {
  if (!modelId) return HUES[0];
  return HUES[Math.max(0, modelId.toLowerCase().charCodeAt(0) - 97) % HUES.length];
}

/** The model with the most messages that day. */
export const topModel = (day: UsageDay) =>
  Object.entries(day.models).sort((a, b) => b[1] - a[1])[0]?.[0];

const mix = (colour: string, share: number) =>
  `color-mix(in srgb, var(--color-${colour}) ${share}%, transparent)`;

/** The fill of a level in light and dark (Tailwind's default palette, as the running app). */
export function heatColours(hue: Hue, level: number): { light: string; dark: string } {
  if (level === 0) return { light: 'var(--color-gray-100)', dark: 'var(--color-gray-800)' };
  if (hue === 'neutral') {
    const light = [200, 400, 600, 800][level - 1];
    return { light: `var(--color-neutral-${light})`, dark: `var(--color-neutral-${1000 - light})` };
  }
  const [light, dark, share] = [
    [100, 900, 40],
    [300, 700, 60],
    [500, 600, 80],
    [700, 500, 100],
  ][level - 1];
  return share === 100
    ? { light: `var(--color-${hue}-${light})`, dark: `var(--color-${hue}-${dark})` }
    : { light: mix(`${hue}-${light}`, share), dark: mix(`${hue}-${dark}`, share) };
}

/** The Monday of a date's week. */
export function weekStart(date: string): string {
  const day = new Date(`${date}T00:00:00Z`);
  day.setUTCDate(day.getUTCDate() - ((day.getUTCDay() + 6) % 7));
  return day.toISOString().slice(0, 10);
}

/** Each day as itself, its week's total or its running total. */
export function showHeat(
  daily: UsageDay[],
  mode: HeatMode,
  weekly: UsageDay[],
  cumulative: UsageDay[],
): UsageDay[] {
  if (mode === 'daily') return daily;
  const totals = new Map((mode === 'weekly' ? weekly : cumulative).map((one) => [one.date, one]));
  return daily.map((day) => {
    const total = totals.get(mode === 'weekly' ? weekStart(day.date) : day.date);
    return total ? { ...total, date: day.date } : day;
  });
}

/** The last whole weeks that fit `columns`, with blanks closing the last column. */
export function heatCells(days: UsageDay[], columns: number): (UsageDay | null)[] {
  if (!days.length) return [];
  const cells: (UsageDay | null)[] = days.slice(-Math.max(7, columns * 7));
  return [...cells, ...Array<null>((7 - (cells.length % 7)) % 7).fill(null)];
}

/** Month names over the columns where each month starts, at least six columns apart. */
export function monthLabels(cells: (UsageDay | null)[], columns: number, locale?: string) {
  const labels: { label: string; column: number; span: number }[] = [];
  let month = '';
  let last = -6;
  cells.forEach((cell, index) => {
    if (!cell || cell.date.slice(0, 7) === month) return;
    month = cell.date.slice(0, 7);
    const column = Math.floor(index / 7) + 1;
    if (column - last < 6) return;
    labels.push({
      label: new Date(`${cell.date}T00:00:00Z`).toLocaleString(locale, {
        month: 'short',
        timeZone: 'UTC',
      }),
      column,
      span: Math.min(6, columns - column + 1),
    });
    last = column;
  });
  return labels;
}
