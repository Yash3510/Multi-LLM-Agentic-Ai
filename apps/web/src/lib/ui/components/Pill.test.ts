import { fireEvent, render } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Pill from './Pill.svelte';
import { COPY_HOLD_MS } from './clipboard';

const HASH = '3f9a21c07be4d58e9a0c6f1b2d7e8a94c51f03b6d2e7a8c9f04b1d6e3a7c5b2f';
const COPY = { label: 'Copy fingerprint', done: 'Copied', failed: 'Could not copy' };

function stubClipboard(writeText: (text: string) => Promise<void>) {
  Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
}

// jsdom has no Web Animations API, which Svelte transitions (the icon swap's fade) run on: finish
// each animation at once.
function stubAnimate() {
  Element.prototype.animate = function () {
    const animation = { onfinish: null as null | (() => void), cancel() {}, playState: 'finished' };
    queueMicrotask(() => animation.onfinish?.());
    return animation as unknown as Animation;
  };
}

describe('Pill', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    stubAnimate();
  });
  afterEach(() => {
    vi.useRealTimers();
    Reflect.deleteProperty(navigator, 'clipboard');
    Reflect.deleteProperty(Element.prototype, 'animate');
  });

  it('formats numbers in the locale, with the unit after a narrow no-break space', () => {
    const { container } = render(Pill, { label: 'Ratio', value: 1234.5, unit: '%' });
    expect(container.textContent).toContain('1,234.5 %');
  });

  it('shows a missing value as a dash and offers no copy', () => {
    const { container, queryByRole } = render(Pill, { label: 'Clause', value: null, copy: COPY });
    expect(container.textContent).toContain('—');
    expect(queryByRole('button')).toBeNull();
  });

  it('shows a hash as 8 characters in Plex Mono, keeps the grouped 64 for paper, copies the raw 64', async () => {
    const writeText = vi.fn(() => Promise.resolve());
    stubClipboard(writeText);
    const { container, getByRole } = render(Pill, { label: 'Fingerprint', hash: HASH, copy: COPY });
    const value = container.querySelector('.font-mono')!;
    expect(value.querySelector('.short')?.textContent).toBe('3f9a21c0…');
    expect(value.querySelector('.full')?.textContent).toBe(HASH.match(/.{4}/g)!.join(' '));

    await fireEvent.click(getByRole('button', { name: 'Copy fingerprint' }));
    expect(writeText).toHaveBeenCalledWith(HASH);
  });

  it('announces the copy, holds the feedback for 1600 ms, then rests', async () => {
    stubClipboard(() => Promise.resolve());
    const { getByRole } = render(Pill, { label: 'Fingerprint', hash: HASH, copy: COPY });
    await fireEvent.click(getByRole('button'));
    // Settles the clipboard promise without moving the clock.
    await vi.advanceTimersByTimeAsync(0);
    expect(getByRole('status').textContent?.trim()).toBe('Copied');

    await vi.advanceTimersByTimeAsync(COPY_HOLD_MS - 1);
    expect(getByRole('status').textContent?.trim()).toBe('Copied');
    await vi.advanceTimersByTimeAsync(1);
    expect(getByRole('status').textContent?.trim()).toBe('');
  });

  it('says so when the browser refuses, and keeps the button name unchanged', async () => {
    stubClipboard(() => Promise.reject(new Error('denied')));
    // jsdom has no copy command either, so the fallback fails too.
    const { getByRole } = render(Pill, { label: 'Fingerprint', hash: HASH, copy: COPY });
    await fireEvent.click(getByRole('button'));
    await vi.advanceTimersByTimeAsync(0);
    expect(getByRole('status').textContent?.trim()).toBe('Could not copy');
    expect(getByRole('button').getAttribute('aria-label')).toBe('Copy fingerprint');
  });
});
