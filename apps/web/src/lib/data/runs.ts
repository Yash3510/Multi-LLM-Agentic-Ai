// Following a run as the screens do (ADR-0035 §3): its events after the last one seen, then each
// new one, until the run ends. A follow that stops before the run ends lost its connection, so
// following again after the last event seen gives the rest, with no gap and no repeat.
import type { DataSource, RunEvent, StreamEvent } from './types';

/** The events after which a run has nothing more to say. */
export const ends = (event: Pick<StreamEvent, 'type'>) =>
  event.type === 'done' || event.type === 'stopped' || event.type === 'error';

/** Waits `ms`, or less when the signal aborts. */
export const sleep = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve) => {
    if (!ms || signal?.aborted) return resolve();
    const done = () => {
      clearTimeout(timer);
      signal?.removeEventListener('abort', done);
      resolve();
    };
    const timer = setTimeout(done, ms);
    signal?.addEventListener('abort', done, { once: true });
  });

/**
 * Follows a run to its end. When the connection drops it waits `retryMs`, then follows again
 * after the last event it saw. Aborting the signal stops following; the run carries on.
 */
export async function* watchRun(
  source: Pick<DataSource, 'followRun'>,
  id: string,
  after: number,
  signal?: AbortSignal,
  retryMs = 1000,
): AsyncGenerator<RunEvent> {
  let seen = after;
  while (!signal?.aborted) {
    for await (const event of source.followRun(id, seen, signal)) {
      seen = event.seq;
      yield event;
      if (ends(event)) return;
    }
    await sleep(retryMs, signal);
  }
}
