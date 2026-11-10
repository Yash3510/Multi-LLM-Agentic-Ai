// Automation schedules (automations look §2): how a schedule is worded and when it next runs.
import type { Schedule } from '$lib/data';

export type { Schedule };

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

const clock = (time: string) => {
  const [hours, minutes] = time.split(':').map(Number);
  return new Date(2000, 0, 1, hours, minutes).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });
};

export function scheduleLabel(schedule: Schedule): string {
  switch (schedule.kind) {
    case 'once':
      return 'Once';
    case 'hourly':
      return 'Hourly';
    case 'daily':
      return `Daily at ${clock(schedule.time)}`;
    case 'weekly':
      return `Weekly at ${clock(schedule.time)} on ${DAYS[schedule.weekday ?? 1]}`;
    case 'weekdays':
      return `Monday – Friday at ${clock(schedule.time)}`;
    case 'monthly':
      return `Monthly at ${clock(schedule.time)}`;
  }
}

/** The first matching time after now (undefined for a one-off). */
export function nextRun(schedule: Schedule, now = new Date()): Date | undefined {
  const [hours, minutes] = schedule.time.split(':').map(Number);
  if (schedule.kind === 'once') return undefined;
  if (schedule.kind === 'hourly') {
    const at = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), minutes);
    if (at <= now) at.setHours(at.getHours() + 1);
    return at;
  }
  for (let day = 0; day <= 31; day++) {
    const at = new Date(now.getFullYear(), now.getMonth(), now.getDate() + day, hours, minutes);
    if (at <= now) continue;
    const weekday = at.getDay();
    if (schedule.kind === 'daily') return at;
    if (schedule.kind === 'weekly' && weekday === (schedule.weekday ?? 1)) return at;
    if (schedule.kind === 'weekdays' && weekday >= 1 && weekday <= 5) return at;
    if (schedule.kind === 'monthly' && at.getDate() === 1) return at;
  }
  return undefined;
}
