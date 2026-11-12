// Motion: the duration and easing tokens for script, the reduced-motion switch on <html data-motion>,
// and the two Svelte transitions everything else uses. The CSS side lives in tokens/motion.css.
import type { TransitionConfig } from 'svelte/transition';

/** Milliseconds, by token name (--duration-*). */
export const DURATION = {
  instant: 100,
  interact: 150,
  quick: 160,
  base: 240,
  calm: 360,
  slow: 560,
  deliberate: 900,
  handover: 1900,
  ambient: 3800,
  menu: 200,
} as const;

/** CSS easing strings, by token name (--ease-out, --ease-in-out, --ease-exit). Linear is for loops only. */
export const EASE = {
  out: 'cubic-bezier(0.22, 1, 0.36, 1)',
  standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
  inOut: 'cubic-bezier(0.45, 0, 0.25, 1)',
  exit: 'cubic-bezier(0.4, 0, 1, 1)',
  cubicOut: 'cubic-bezier(0.33, 1, 0.68, 1)',
  expo: 'cubic-bezier(0.16, 1, 0.3, 1)',
  spring:
    'linear(0, 0.0827 4.2%, 0.2594 8.3%, 0.4563 12.5%, 0.634 16.7%, 0.776 20.8%, 0.8792 25%, 0.9481 29.2%, 0.9898 33.3%, 1.0119 37.5%, 1.021 41.7%, 1.0224 45.8%, 1.0198 50%, 1.0156 54.2%, 1.0112 58.3%, 1.0074 62.5%, 1.0044 66.7%, 1.0023 70.8%, 1.0009 75%, 1.0001 79.2%, 0.9997 83.3%, 0.9995 87.5%, 0.9995 91.7%, 0.9996 95.8%, 1)',
  linear: 'linear',
} as const;

export type MotionSetting = 'system' | 'reduce';

const KEY = '4ce.motion';
const SETTINGS: readonly string[] = ['system', 'reduce'];
/** Reduced motion keeps crossfades, at this length or less. */
const REDUCED_MS = 120;
/** Entrances move 8 px at most. */
const MAX_RISE = 8;

function stored(): MotionSetting {
  try {
    const value = localStorage.getItem(KEY);
    return value && SETTINGS.includes(value) ? (value as MotionSetting) : 'system';
  } catch {
    return 'system'; // Storage is blocked: follow the system.
  }
}

// Optional because jsdom, which component tests run in, has no matchMedia.
const systemQuery = globalThis.matchMedia?.('(prefers-reduced-motion: reduce)');

let setting = $state(stored());
let systemReduce = $state(systemQuery?.matches ?? false);

const isReduced = () => setting === 'reduce' || systemReduce;

function apply() {
  if (isReduced()) document.documentElement.dataset.motion = 'reduce';
  else delete document.documentElement.dataset.motion;
}

systemQuery?.addEventListener('change', (event) => {
  systemReduce = event.matches;
  apply();
});
apply();

export const motion = {
  get setting(): MotionSetting {
    return setting;
  },
  set setting(value: MotionSetting) {
    if (!SETTINGS.includes(value)) return;
    setting = value;
    try {
      localStorage.setItem(KEY, value);
    } catch {
      // Storage is blocked: the choice lasts until the page reloads.
    }
    apply();
  },
  /** True when either the user or the system asks for reduced motion. */
  get reduced(): boolean {
    return isReduced();
  },
};

/** A CSS cubic-bezier() as an easing function for Svelte, solved by bisection on x. */
function bezier(css: string): (x: number) => number {
  const [x1, y1, x2, y2] = (css.match(/[\d.]+/g) ?? []).map(Number);
  const at = (p1: number, p2: number, t: number) =>
    3 * p1 * t * (1 - t) ** 2 + 3 * p2 * t ** 2 * (1 - t) + t ** 3;
  return (x) => {
    if (x <= 0 || x >= 1) return x;
    let low = 0;
    let high = 1;
    for (let i = 0; i < 24; i++) {
      const mid = (low + high) / 2;
      if (at(x1, x2, mid) < x) low = mid;
      else high = mid;
    }
    return at(y1, y2, (low + high) / 2);
  };
}

const easeOut = bezier(EASE.out);
const easeExit = bezier(EASE.exit);

type Options = { direction?: 'in' | 'out' | 'both' };

export interface FadeParams {
  delay?: number;
  duration?: number;
}

export interface RiseParams extends FadeParams {
  /** Pixels travelled, clamped to 8 either way. Positive rises from below; negative drops from above. */
  y?: number;
}

/** Arrivals ease out; an out: transition is an exit, so it takes two thirds of the time and eases away. */
function timing(duration: number, { direction }: Options) {
  return direction === 'out'
    ? { duration: Math.round((duration * 2) / 3), easing: easeExit }
    : { duration, easing: easeOut };
}

/** Opacity only. Under reduced motion, the same fade capped at 120 ms. */
export function fade(
  node: Element,
  { delay = 0, duration = DURATION.base }: FadeParams = {},
  options: Options = {},
): TransitionConfig {
  const opacity = +getComputedStyle(node).opacity;
  const css = (t: number) => `opacity: ${t * opacity}`;
  if (motion.reduced) return { delay, duration: Math.min(duration, REDUCED_MS), css };
  return { delay, ...timing(duration, options), css };
}

/** Opacity plus at most 8 px of vertical travel. Under reduced motion it becomes fade's crossfade. */
export function rise(
  node: Element,
  { delay = 0, duration = DURATION.calm, y = MAX_RISE }: RiseParams = {},
  options: Options = {},
): TransitionConfig {
  if (motion.reduced) return fade(node, { delay, duration }, options);
  const style = getComputedStyle(node);
  const opacity = +style.opacity;
  // Keep the node's own transform and add the travel after it.
  const transform = style.transform === 'none' ? '' : `${style.transform} `;
  const distance = Math.max(-MAX_RISE, Math.min(MAX_RISE, y));
  return {
    delay,
    ...timing(duration, options),
    css: (t, u) => `opacity: ${t * opacity}; transform: ${transform}translateY(${u * distance}px)`,
  };
}
