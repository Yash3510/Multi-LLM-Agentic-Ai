// How long ago, as the workspace lists show it ("2 months ago"): the largest whole unit.
const relative = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
const STEPS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 31_536_000],
  ['month', 2_592_000],
  ['day', 86_400],
  ['hour', 3600],
  ['minute', 60],
];

export function ago(when: Date, now = new Date()) {
  const seconds = (when.getTime() - now.getTime()) / 1000;
  const [unit, size] = STEPS.find(([, step]) => Math.abs(seconds) >= step) ?? ['second', 1];
  return relative.format(Math.round(seconds / size), unit);
}

/** The full date, for the tooltip on a relative time. */
export const longDate = new Intl.DateTimeFormat('en', { dateStyle: 'full', timeStyle: 'short' });
