import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const root = document.documentElement;
const load = async () => (await import('./density.svelte')).density;

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
  root.removeAttribute('data-density');
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('density', () => {
  it('starts at default and applies it to <html>', async () => {
    expect((await load()).value).toBe('default');
    expect(root.dataset.density).toBe('default');
  });

  it('stores a choice under 4ce.density and restores it on the next load', async () => {
    const density = await load();
    density.value = 'compact';
    expect(localStorage.getItem('4ce.density')).toBe('compact');
    expect(root.dataset.density).toBe('compact');

    vi.resetModules();
    root.removeAttribute('data-density');
    expect((await load()).value).toBe('compact');
    expect(root.dataset.density).toBe('compact');
  });

  it('ignores stored and assigned values outside the contract', async () => {
    localStorage.setItem('4ce.density', 'cosy');
    const density = await load();
    expect(density.value).toBe('default');
    density.value = 'cosy' as never;
    expect(root.dataset.density).toBe('default');
  });

  it('keeps working when storage is blocked', async () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const density = await load();
    density.value = 'comfortable';
    expect(root.dataset.density).toBe('comfortable');
  });
});
