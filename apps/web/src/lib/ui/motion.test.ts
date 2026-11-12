import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Read from disk: Vitest does not process CSS, so a ?raw import comes back empty.
const motionCss = readFileSync(join(import.meta.dirname, 'tokens/motion.css'), 'utf8');
const appCss = readFileSync(join(import.meta.dirname, '../../app.css'), 'utf8');

const REDUCE = '(prefers-reduced-motion: reduce)';
const root = document.documentElement;

/** Stubs matchMedia with fixed answers and returns a way to fire a system change. */
function system(matches: Record<string, boolean>) {
  const listeners = new Map<string, (event: { matches: boolean }) => void>();
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: matches[query] ?? false,
    addEventListener: (_: string, listener: (event: { matches: boolean }) => void) =>
      listeners.set(query, listener),
  }));
  return (query: string, value: boolean) => listeners.get(query)?.({ matches: value });
}

const load = () => import('./motion.svelte');
const node = () => document.createElement('div');

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
  root.removeAttribute('data-motion');
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('motion tokens', () => {
  it('match the CSS variables in tokens/motion.css', async () => {
    const { DURATION, EASE } = await load();
    for (const [name, ms] of Object.entries(DURATION)) {
      expect(motionCss).toContain(`--duration-${name}: ${ms}ms;`);
    }
    expect(motionCss).toContain(`--ease-out: ${EASE.out};`);
    expect(motionCss).toContain(`--ease-in-out: ${EASE.inOut};`);
    expect(motionCss).toContain(`--ease-exit: ${EASE.exit};`);
    expect(motionCss).toContain(`--ease-cubic-out: ${EASE.cubicOut};`);
    expect(DURATION.menu).toBe(200);
  });

  it('adds the expo arrival curve and one spring, mirrored in CSS (ADR-0042)', async () => {
    const { EASE } = await load();
    expect(motionCss).toContain(`--ease-expo: ${EASE.expo};`);
    // The formatter wraps the long value, so the spring is compared with whitespace removed.
    const bare = (text: string) => text.replaceAll(/\s+/g, '');
    expect(bare(motionCss)).toContain(bare(`--ease-spring: ${EASE.spring};`));
  });

  it('times hover, press and focus at 150 ms on the standard curve, the same in and out (ADR-0042)', async () => {
    const { DURATION, EASE } = await load();
    expect(DURATION.interact).toBe(150);
    expect(DURATION.instant).toBe(100);
    expect(motionCss).toContain(`--ease-standard: ${EASE.standard};`);
    expect(appCss).toContain(
      'transition-duration: var(--interact-duration, var(--duration-interact)) !important;',
    );
    expect(appCss).toContain('transition-timing-function: var(--ease-standard) !important;');
    // No slower leave: the old rule held a hover for 240 ms on the way out.
    expect(appCss).not.toContain('transition-duration: var(--duration-base) !important;');
  });

  it('keeps the spring gentle: it peaks at 3 % or less and settles at 1', async () => {
    const { EASE } = await load();
    const stops = EASE.spring
      .slice('linear('.length, -1)
      .split(', ')
      .map((stop) => Number.parseFloat(stop));
    expect(stops[0]).toBe(0);
    expect(stops.at(-1)).toBe(1);
    expect(Math.max(...stops)).toBeGreaterThan(1);
    expect(Math.max(...stops)).toBeLessThanOrEqual(1.03);
  });
});

describe('motion setting', () => {
  it('is reduced when the system asks, and follows a live system change', async () => {
    const change = system({ [REDUCE]: true });
    const { motion } = await load();
    expect(motion.setting).toBe('system');
    expect(motion.reduced).toBe(true);
    expect(root.dataset.motion).toBe('reduce');

    change(REDUCE, false);
    expect(motion.reduced).toBe(false);
    expect(root.hasAttribute('data-motion')).toBe(false);
  });

  it('stays reduced when the user chose reduce, whatever the system does', async () => {
    const change = system({ [REDUCE]: false });
    const { motion } = await load();
    motion.setting = 'reduce';
    expect(localStorage.getItem('4ce.motion')).toBe('reduce');
    expect(root.dataset.motion).toBe('reduce');
    change(REDUCE, true);
    change(REDUCE, false);
    expect(motion.reduced).toBe(true);

    motion.setting = 'system';
    expect(root.hasAttribute('data-motion')).toBe(false);
  });

  it('restores a stored setting and ignores values outside the contract', async () => {
    localStorage.setItem('4ce.motion', 'reduce');
    expect((await load()).motion.reduced).toBe(true);

    vi.resetModules();
    localStorage.setItem('4ce.motion', 'fast');
    const { motion } = await load();
    expect(motion.setting).toBe('system');
    motion.setting = 'fast' as never;
    expect(motion.setting).toBe('system');
  });

  it('keeps working when storage is blocked', async () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const { motion } = await load();
    expect(motion.setting).toBe('system');
    motion.setting = 'reduce';
    expect(root.dataset.motion).toBe('reduce');
  });
});

describe('fade and rise', () => {
  const samples = Array.from({ length: 101 }, (_, i) => i / 100);

  it('fade arrives over base with ease-out, and leaves in two thirds of the time', async () => {
    const { fade, DURATION } = await load();
    const arrive = fade(node());
    expect(arrive.duration).toBe(DURATION.base);
    expect(arrive.css?.(0.25, 0.75)).toBe('opacity: 0.25');
    expect(arrive.easing?.(0.5)).toBeGreaterThan(0.5);

    const leave = fade(node(), {}, { direction: 'out' });
    expect(leave.duration).toBe(160);
    expect(leave.easing?.(0.5)).toBeLessThan(0.5);
  });

  it('eases without overshoot: every curve stays within 0 to 1 and never turns back', async () => {
    const { fade } = await load();
    for (const direction of ['in', 'out'] as const) {
      const ease = fade(node(), {}, { direction }).easing!;
      const values = samples.map(ease);
      expect(values[0]).toBe(0);
      expect(values[100]).toBe(1);
      values.forEach((value, i) => {
        expect(value).toBeGreaterThanOrEqual(i ? values[i - 1] : 0);
        expect(value).toBeLessThanOrEqual(1);
      });
    }
  });

  it('rise travels at most 8 px, in either direction, over calm', async () => {
    const { rise, DURATION } = await load();
    const start = rise(node());
    expect(start.duration).toBe(DURATION.calm);
    expect(start.css?.(0, 1)).toBe('opacity: 0; transform: translateY(8px)');
    expect(start.css?.(1, 0)).toBe('opacity: 1; transform: translateY(0px)');
    expect(rise(node(), { y: 40 }).css?.(0, 1)).toContain('translateY(8px)');
    expect(rise(node(), { y: -20 }).css?.(0, 1)).toContain('translateY(-8px)');
  });

  it('becomes an opacity-only crossfade of 120 ms at most when motion is reduced', async () => {
    system({ [REDUCE]: true });
    const { fade, rise } = await load();
    for (const config of [
      fade(node()),
      rise(node()),
      rise(node(), { duration: 560, delay: 40 }, { direction: 'out' }),
    ]) {
      expect(config.duration).toBeLessThanOrEqual(120);
      expect(config.css?.(0.5, 0.5)).toBe('opacity: 0.5');
    }
    expect(rise(node(), { delay: 40 }).delay).toBe(40);
    expect(fade(node(), { duration: 100 }).duration).toBe(100);
  });
});
