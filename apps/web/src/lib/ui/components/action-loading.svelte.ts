// The loading state's clock (design-system.md "States"): the six-dot ring appears only after
// 300 ms, so quick actions never flash it, and the elapsed time joins it after 10 s.

export const RING_AFTER = 300;
export const ELAPSED_AFTER = 10_000;

/** waiting: loading but nothing shown yet; ring: the six-dot ring; timed: the ring and elapsed time. */
export type LoadingPhase = 'idle' | 'waiting' | 'ring' | 'timed';

export interface LoadingClock {
  readonly phase: LoadingPhase;
  /** Whole seconds since loading began. */
  readonly seconds: number;
}

/** What a loading control shows `ms` after it began; null when it is not loading. */
export function loadingPhase(ms: number | null): LoadingPhase {
  if (ms === null) return 'idle';
  if (ms < RING_AFTER) return 'waiting';
  return ms < ELAPSED_AFTER ? 'ring' : 'timed';
}

/** Times one control's loading. Call it while the component is being set up. */
export function loadingClock(loading: () => boolean): LoadingClock {
  let elapsed = $state<number | null>(null);

  $effect(() => {
    if (!loading()) {
      elapsed = null;
      return;
    }
    const start = Date.now();
    elapsed = 0;
    // Measured from the start on every tick, so a late timer never drifts the count.
    const tick = () => (elapsed = Date.now() - start);
    let everySecond: ReturnType<typeof setInterval> | undefined;
    const ring = setTimeout(tick, RING_AFTER);
    const timed = setTimeout(() => {
      tick();
      everySecond = setInterval(tick, 1000);
    }, ELAPSED_AFTER);
    return () => {
      clearTimeout(ring);
      clearTimeout(timed);
      clearInterval(everySecond);
    };
  });

  return {
    get phase() {
      return loadingPhase(elapsed);
    },
    get seconds() {
      return Math.floor((elapsed ?? 0) / 1000);
    },
  };
}
