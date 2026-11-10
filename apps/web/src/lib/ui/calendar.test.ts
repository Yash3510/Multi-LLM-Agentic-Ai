import { describe, expect, it } from 'vitest';
import type { CalendarEvent } from '$lib/data';
import { occurrences } from './calendar';

const event = (repeat: CalendarEvent['repeat']): CalendarEvent => ({
  id: 'e1',
  calendarId: 'c',
  title: 'Review',
  start: new Date(2026, 10, 2, 9),
  end: new Date(2026, 10, 2, 10),
  allDay: false,
  repeat,
  reminder: 'none',
  location: '',
  description: '',
});

describe('calendar repeats', () => {
  it('expands repeating events within a range', () => {
    const from = new Date(2026, 10, 1);
    const to = new Date(2026, 11, 1);
    expect(occurrences([event('none')], from, to)).toHaveLength(1);
    expect(occurrences([event('daily')], from, to)).toHaveLength(29);
    expect(occurrences([event('weekly')], from, to).map((one) => one.start.getDate())).toEqual([
      2, 9, 16, 23, 30,
    ]);
    expect(
      occurrences([event('monthly')], new Date(2026, 10, 1), new Date(2027, 1, 1)),
    ).toHaveLength(3);
    expect(occurrences([event('yearly')], from, new Date(2028, 11, 1))).toHaveLength(3);
    const [second] = occurrences([event('weekly')], new Date(2026, 10, 9), to);
    expect(second.end.getTime() - second.start.getTime()).toBe(3_600_000);
  });
});
