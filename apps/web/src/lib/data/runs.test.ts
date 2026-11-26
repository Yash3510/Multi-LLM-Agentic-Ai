import { describe, expect, it } from 'vitest';
import { createFakeSource } from './fake';
import { watchRun } from './runs';
import type { DataSource, RunEvent } from './types';

describe('watchRun', () => {
  it('follows again after a dropped connection, with no gap and no repeat, to the end', async () => {
    const source = createFakeSource({ pace: 0 });
    const id = await source.ask('c-0142', 'What if the connection drops?');
    const afters: number[] = [];
    const counting: Pick<DataSource, 'followRun'> = {
      followRun: (run, after, signal) => {
        afters.push(after);
        return source.followRun(run, after, signal);
      },
    };
    const seen: RunEvent[] = [];
    for await (const event of watchRun(counting, id, 0, { retryMs: 0 })) {
      seen.push(event);
      if (event.type === 'sign-off') void source.decide(id, 'released');
    }
    expect(seen.map((event) => event.seq)).toEqual(seen.map((_, index) => index + 1));
    expect(seen.at(-1)?.type).toBe('done');
    // Followed twice: from the start, then after the last event before the drop.
    expect(afters).toHaveLength(2);
    expect(afters[1]).toBeGreaterThan(0);
  });

  it('says when it starts reconnecting and when it follows again', async () => {
    const source = createFakeSource({ pace: 0 });
    const reconnecting: boolean[] = [];
    const watch = async (question: string) => {
      const id = await source.ask('c-0142', question);
      const options = { retryMs: 0, onreconnecting: (state: boolean) => reconnecting.push(state) };
      for await (const event of watchRun(source, id, 0, options)) {
        if (event.type === 'sign-off') void source.decide(id, 'released');
      }
    };
    await watch('Is R2 within the limit?');
    expect(reconnecting).toEqual([]);
    await watch('What if the connection drops?');
    expect(reconnecting).toEqual([true, false]);
  });
});
