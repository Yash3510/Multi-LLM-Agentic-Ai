import { describe, expect, it } from 'vitest';
import { nextRun, scheduleLabel } from './automations';

describe('automation schedules (automations look §2)', () => {
  it('words each schedule like the running app', () => {
    expect(scheduleLabel({ kind: 'daily', time: '09:00' })).toBe('Daily at 9:00 AM');
    expect(scheduleLabel({ kind: 'weekly', time: '14:30', weekday: 1 })).toBe(
      'Weekly at 2:30 PM on Monday',
    );
    expect(scheduleLabel({ kind: 'weekdays', time: '08:00' })).toBe('Monday – Friday at 8:00 AM');
    expect(scheduleLabel({ kind: 'hourly', time: '00:15' })).toBe('Hourly');
    expect(scheduleLabel({ kind: 'once', time: '10:00' })).toBe('Once');
  });

  it('finds the next run', () => {
    const now = new Date(2026, 10, 10, 10, 0); // a Tuesday
    expect(nextRun({ kind: 'daily', time: '09:00' }, now)).toEqual(new Date(2026, 10, 11, 9, 0));
    expect(nextRun({ kind: 'daily', time: '11:00' }, now)).toEqual(new Date(2026, 10, 10, 11, 0));
    expect(nextRun({ kind: 'weekdays', time: '08:00' }, new Date(2026, 10, 13, 9, 0))).toEqual(
      new Date(2026, 10, 16, 8, 0),
    );
    expect(nextRun({ kind: 'hourly', time: '00:15' }, now)).toEqual(new Date(2026, 10, 10, 10, 15));
  });
});
