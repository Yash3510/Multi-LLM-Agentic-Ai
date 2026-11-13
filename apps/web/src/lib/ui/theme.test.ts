import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const DARK = '(prefers-color-scheme: dark)';
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

const load = async () => (await import('./theme.svelte')).theme;

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
  root.removeAttribute('data-theme');
  root.style.colorScheme = '';
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('theme', () => {
  it('follows the system by default and applies the result to <html>', async () => {
    system({ [DARK]: true });
    const theme = await load();
    expect(theme.choice).toBe('system');
    expect(theme.resolved).toBe('dark');
    expect(root.dataset.theme).toBe('dark');
    expect(root.style.colorScheme).toBe('dark');
  });

  it('follows a live system change only while the choice is system', async () => {
    const change = system({ [DARK]: false });
    const theme = await load();
    change(DARK, true);
    expect(root.dataset.theme).toBe('dark');

    theme.choice = 'light';
    change(DARK, false);
    change(DARK, true);
    expect(theme.resolved).toBe('light');
    expect(root.dataset.theme).toBe('light');
  });

  it('stores a choice under 4ce.theme and restores it on the next load', async () => {
    system({ [DARK]: false });
    const theme = await load();
    theme.choice = 'dark';
    expect(localStorage.getItem('4ce.theme')).toBe('dark');
    expect(root.dataset.theme).toBe('dark');

    vi.resetModules();
    root.removeAttribute('data-theme');
    expect((await load()).choice).toBe('dark');
    expect(root.dataset.theme).toBe('dark');
  });

  it('offers OLED Dark: dark, with pure black greys marked on <html>', async () => {
    system({ [DARK]: false });
    const theme = await load();
    theme.choice = 'oled-dark';
    expect(theme.resolved).toBe('dark');
    expect(root.dataset.theme).toBe('dark');
    expect(root.dataset.oled).toBe('');
    theme.choice = 'light';
    expect(root.hasAttribute('data-oled')).toBe(false);
  });

  it('ignores stored and assigned values outside the contract', async () => {
    system({ [DARK]: false });
    localStorage.setItem('4ce.theme', 'sepia');
    const theme = await load();
    expect(theme.choice).toBe('system');
    theme.choice = 'sepia' as never;
    expect(theme.choice).toBe('system');
    expect(localStorage.getItem('4ce.theme')).toBe('sepia');
  });

  it('keeps working when storage is blocked', async () => {
    system({ [DARK]: true });
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const theme = await load();
    expect(theme.resolved).toBe('dark');
    theme.choice = 'light';
    expect(root.dataset.theme).toBe('light');
  });

  it('works without matchMedia (jsdom, very old engines) and resolves system to light', async () => {
    const theme = await load();
    expect(theme.resolved).toBe('light');
  });

  it('is reactive, so components re-render when the theme changes', async () => {
    system({ [DARK]: false });
    const theme = await load();
    // Imported after the module reset so they share the store's copy of the Svelte runtime.
    const { flushSync } = await import('svelte');
    const { toStore } = await import('svelte/store');
    const seen: string[] = [];
    const unsubscribe = toStore(() => theme.resolved).subscribe((value) => seen.push(value));
    theme.choice = 'dark';
    flushSync();
    unsubscribe();
    expect(seen).toEqual(['light', 'dark']);
  });
});
