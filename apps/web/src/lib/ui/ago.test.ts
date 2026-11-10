import { describe, expect, it } from 'vitest';
import { calendarDay } from './ago';

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
