import { describe, expect, it } from 'vitest';
import { calendarDay, shortAgo } from './ago';

describe('calendar day (dayjs calendar wording)', () => {
  // Local-time constructors, so the tests hold in any time zone. 12 Nov 2026 is a Thursday.
  const now = new Date(2026, 10, 12, 9, 0);
  it('says Today, Yesterday, Last weekday, then the short date', () => {
    expect(calendarDay(new Date(2026, 10, 12, 1, 0), now)).toBe('Today');
    expect(calendarDay(new Date(2026, 10, 11, 23, 0), now)).toBe('Yesterday');
    expect(calendarDay(new Date(2026, 10, 7, 12, 0), now)).toBe('Last Saturday');
    expect(calendarDay(new Date(2026, 10, 5, 12, 0), now)).toBe('11/05/2026');
    expect(calendarDay(new Date(2026, 10, 13, 12, 0), now)).toBe('Tomorrow');
  });
});

describe('shortAgo', () => {
  const now = new Date('2026-11-13T12:00:00Z');
  const back = (seconds: number) => new Date(now.getTime() - seconds * 1000);

  it.each([
    [0, 'now'],
    [59, 'now'],
    [60, '1m'],
    [59 * 60, '59m'],
    [2 * 3600, '2h'],
    [23 * 3600, '23h'],
    [86_400, '1d'],
    [6 * 86_400, '6d'],
    [7 * 86_400, '1w'],
    [29 * 86_400, '4w'],
    [30 * 86_400, '1mo'],
    [330 * 86_400, '11mo'],
    [365 * 86_400, '1y'],
  ])('%i seconds back reads %s', (seconds, words) => {
    expect(shortAgo(back(seconds), now)).toBe(words);
  });

  it('reads a time ahead of the clock as now', () => {
    expect(shortAgo(back(-500), now)).toBe('now');
  });
});
