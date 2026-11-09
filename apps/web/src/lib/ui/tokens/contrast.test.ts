// Measures what ships: the semantic roles are read from the token files and resolved to their hex
// primitives. It pins the grey ramp and every role to the values measured from the running app
// (ADR-0041), so a token cannot drift from the look, and keeps the contrast floors that the look
// itself meets: body text, the focus ring and the verdict text.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

// Read from disk: Vitest does not process CSS, so a ?raw import comes back empty.
const read = (file: string) => readFileSync(join(import.meta.dirname, file), 'utf8');

type Rgb = [number, number, number];

const primitives = new Map(
  [...read('primitives.css').matchAll(/--ref-([\w-]+):\s*(#[0-9a-f]{6});/gi)].map(
    ([, name, value]) => [name, value.toLowerCase()],
  ),
);

/** Role name to primitive name, for every --color-* role that points at a primitive. The grey
 * ramp's own utilities (--color-gray-*) are the ramp, not roles, so they are left out. */
const roles = (css: string) =>
  new Map(
    [...css.matchAll(/--color-([\w-]+):\s*var\(--ref-([\w-]+)\)/g)]
      .filter(([, role]) => !role.startsWith('gray-'))
      .map(([, role, ref]) => [role, ref]),
  );

const THEMES = { light: roles(read('theme.css')), dark: roles(read('dark.css')) };
type Theme = keyof typeof THEMES;

const rgb = (hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)) as Rgb;

/** WCAG 2 relative luminance and contrast ratio. */
const decode = (c: number) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const luminance = ([r, g, b]: Rgb) =>
  0.2126 * decode(r / 255) + 0.7152 * decode(g / 255) + 0.0722 * decode(b / 255);
const contrast = (x: string, y: string) => {
  const [high, low] = [luminance(rgb(x)), luminance(rgb(y))].sort((p, q) => q - p);
  return (high + 0.05) / (low + 0.05);
};

function colour(theme: Theme, role: string): string {
  const ref = THEMES[theme].get(role);
  const value = ref && primitives.get(ref);
  if (!value) throw new Error(`${theme} --color-${role} does not resolve to a primitive`);
  return value;
}

// data-and-logic look §3: the neutral ramp at its default boot values.
const RAMP = {
  'gray-50': '#f8f8f8',
  'gray-100': '#ebebeb',
  'gray-200': '#e4e4e4',
  'gray-300': '#cecece',
  'gray-400': '#b4b4b4',
  'gray-500': '#9b9b9b',
  'gray-600': '#666666',
  'gray-700': '#4d4d4d',
  'gray-800': '#333333',
  'gray-850': '#262626',
  'gray-900': '#161616',
  'gray-950': '#0d0d0d',
};

// Each role at the measured value it stands for: shell, menu and sidebar surfaces, hairlines,
// text tiers, the 4CE violet, the blue focus ring and the status-badge verdict text (common F31).
const MEASURED: Record<Theme, Record<string, string>> = {
  light: {
    'surface-page': '#ffffff',
    'surface-raised': '#ffffff',
    'surface-sunken': '#f8f8f8',
    'surface-hover': '#ebebeb',
    'line-1': '#ebebeb',
    'line-2': '#e4e4e4',
    'line-control': '#cecece',
    'ink-1': '#161616',
    'ink-2': '#4d4d4d',
    'ink-3': '#9b9b9b',
    'ink-disabled': '#b4b4b4',
    solid: '#000000',
    'on-solid': '#ffffff',
    'solid-hover': '#0d0d0d',
    accent: '#7c3aed',
    'accent-head': '#7c3aed',
    'accent-tail': '#8b5cf6',
    focus: '#2b7fff',
    ok: '#008236',
    'ok-mark': '#00c950',
    caution: '#a65f00',
    'caution-mark': '#f0b100',
    stop: '#c10007',
    'stop-mark': '#fb2c36',
    'intro-ink': '#0d1117',
    'intro-ground': '#ffffff',
    'mark-tile': '#0d1117',
  },
  dark: {
    'surface-page': '#161616',
    'surface-raised': '#262626',
    'surface-sunken': '#0d0d0d',
    'surface-hover': '#333333',
    'line-1': '#333333',
    'line-2': '#4d4d4d',
    'line-control': '#666666',
    'ink-1': '#ffffff',
    'ink-2': '#cecece',
    'ink-3': '#b4b4b4',
    'ink-disabled': '#666666',
    solid: '#ffffff',
    'on-solid': '#000000',
    'solid-hover': '#ebebeb',
    accent: '#c4b5fd',
    'accent-head': '#ddd6fe',
    'accent-tail': '#a78bfa',
    focus: '#2b7fff',
    ok: '#b9f8cf',
    'ok-mark': '#00c950',
    caution: '#fff085',
    'caution-mark': '#f0b100',
    stop: '#ffc9c9',
    'stop-mark': '#fb2c36',
    'intro-ink': '#ffffff',
    'intro-ground': '#161616',
    'mark-tile': '#0d1117',
  },
};

describe('contrast measurement', () => {
  it('matches the WCAG formula', () => {
    expect(contrast('#000000', '#ffffff')).toBe(21);
    expect(contrast('#9b9b9b', '#ffffff')).toBeCloseTo(2.78, 2);
  });
});

describe('grey ramp', () => {
  it('ships the measured ramp', () => {
    const shipped = Object.fromEntries(
      Object.keys(RAMP).map((step) => [step, primitives.get(step)]),
    );
    expect(shipped).toEqual(RAMP);
  });
});

describe.each(Object.keys(THEMES) as Theme[])('%s theme', (theme) => {
  it('defines the same roles as the other theme', () => {
    expect([...THEMES[theme].keys()].sort()).toEqual([...THEMES.light.keys()].sort());
  });

  it('ships exactly the measured values', () => {
    const shipped = Object.fromEntries(
      Object.keys(MEASURED[theme]).map((role) => [role, colour(theme, role)]),
    );
    expect(shipped).toEqual(MEASURED[theme]);
  });

  // The look's own floors. Muted ink-3 sits below 4.5:1 by design (ADR-0041); accessibility mode
  // raises it.
  it('gives body text and verdict text at least 4.5:1 on page and raised surfaces', () => {
    const low = ['ink-1', 'ink-2', 'ok', 'caution', 'stop'].flatMap((fg) =>
      ['surface-page', 'surface-raised'].flatMap((bg) => {
        const ratio = contrast(colour(theme, fg), colour(theme, bg));
        return ratio < 4.5 ? [`${fg} on ${bg}: ${ratio.toFixed(2)}`] : [];
      }),
    );
    expect(low).toEqual([]);
  });

  it('gives the focus ring at least 3:1 on page and raised surfaces', () => {
    for (const bg of ['surface-page', 'surface-raised'])
      expect(contrast(colour(theme, 'focus'), colour(theme, bg))).toBeGreaterThanOrEqual(3);
  });
});
