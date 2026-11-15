import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { dismiss, hold, release, toast, toasts } from './toast.svelte';

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  for (const one of [...toasts.list]) dismiss(one.id);
  vi.useRealTimers();
});

describe('toast', () => {
  it('shows a message and hides it after four seconds', () => {
    toast('Settings saved successfully!');
    expect(toasts.list.map((one) => one.message)).toEqual(['Settings saved successfully!']);
    vi.advanceTimersByTime(3999);
    expect(toasts.list).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(toasts.list).toHaveLength(0);
  });

  it('stays while held and gets four more seconds on release', () => {
    const id = toast('Saved');
    vi.advanceTimersByTime(2000);
    hold(id);
    vi.advanceTimersByTime(10000);
    expect(toasts.list).toHaveLength(1);
    release(id);
    vi.advanceTimersByTime(3999);
    expect(toasts.list).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(toasts.list).toHaveLength(0);
  });

  it('closes one toast on request and keeps the others', () => {
    const first = toast('One');
    toast('Two', 'error');
    dismiss(first);
    expect(toasts.list.map((one) => [one.message, one.kind])).toEqual([['Two', 'error']]);
  });
});
