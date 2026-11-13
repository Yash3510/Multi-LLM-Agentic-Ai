// How long ago, worded as the running app words it ("a few seconds ago", "a day ago",
// "2 months ago"): its thresholds round to the nearest whole unit and say "a"/"an" for one.
const MINUTE = 60;
const HOUR = 3600;
const DAY = 86_400;

/** [upper bound in seconds, words] in order; a function gets the elapsed seconds. */
const STEPS: [number, (seconds: number) => string][] = [
  [45, () => 'a few seconds'],
  [90, () => 'a minute'],
  [45 * MINUTE, (s) => `${Math.round(s / MINUTE)} minutes`],
  [90 * MINUTE, () => 'an hour'],
  [22 * HOUR, (s) => `${Math.round(s / HOUR)} hours`],
  [36 * HOUR, () => 'a day'],
  [26 * DAY, (s) => `${Math.round(s / DAY)} days`],
  [46 * DAY, () => 'a month'],
  [320 * DAY, (s) => `${Math.round(s / (30.4 * DAY))} months`],
  [548 * DAY, () => 'a year'],
  [Infinity, (s) => `${Math.round(s / (365 * DAY))} years`],
];

export function ago(when: Date, now = new Date()) {
  const seconds = Math.max(0, (now.getTime() - when.getTime()) / 1000);
  const [, words] = STEPS.find(([limit]) => seconds < limit) ?? STEPS[STEPS.length - 1];
  return `${words(seconds)} ago`;
}

/** The full date, for the tooltip on a relative time. */
export const longDate = new Intl.DateTimeFormat('en', { dateStyle: 'full', timeStyle: 'short' });

const WEEKDAY = new Intl.DateTimeFormat('en', { weekday: 'long' });

/** A date as dayjs's calendar words it: Today, Yesterday, Tomorrow, a weekday within the week
 * either side ("Last Saturday"), else MM/DD/YYYY. Days count from the start of today. */
export function calendarDay(when: Date, now = new Date()) {
  const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = (when.getTime() - midnight.getTime()) / (DAY * 1000);
  if (days < -6 || days >= 7) {
    const pad = (value: number) => String(value).padStart(2, '0');
    return `${pad(when.getMonth() + 1)}/${pad(when.getDate())}/${when.getFullYear()}`;
  }
  if (days < -1) return `Last ${WEEKDAY.format(when)}`;
  if (days < 0) return 'Yesterday';
  if (days < 1) return 'Today';
  if (days < 2) return 'Tomorrow';
  return WEEKDAY.format(when);
}
