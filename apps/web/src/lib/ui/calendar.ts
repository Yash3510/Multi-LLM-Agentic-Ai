// Calendar repeats (calendar look §1): each event's occurrences inside a range.
import type { CalendarEvent } from '$lib/data';

const next = (date: Date, repeat: CalendarEvent['repeat']) => {
  const at = new Date(date);
  if (repeat === 'daily') at.setDate(at.getDate() + 1);
  else if (repeat === 'weekly') at.setDate(at.getDate() + 7);
  else if (repeat === 'monthly') at.setMonth(at.getMonth() + 1);
  else if (repeat === 'yearly') at.setFullYear(at.getFullYear() + 1);
  return at;
};

/** Every occurrence that starts in [from, to), keeping each event's length. */
export function occurrences(events: CalendarEvent[], from: Date, to: Date): CalendarEvent[] {
  const out: CalendarEvent[] = [];
  for (const event of events) {
    const length = event.end.getTime() - event.start.getTime();
    let start = new Date(event.start);
    for (let guard = 0; start < to && guard < 2000; guard++) {
      if (start >= from) out.push({ ...event, start, end: new Date(start.getTime() + length) });
      if (event.repeat === 'none') break;
      start = next(start, event.repeat);
    }
  }
  return out.sort((a, b) => a.start.getTime() - b.start.getTime());
}
