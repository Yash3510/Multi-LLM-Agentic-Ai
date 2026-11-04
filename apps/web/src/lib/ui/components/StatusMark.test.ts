import { render } from '@testing-library/svelte';
import { flushSync } from 'svelte';
import { describe, expect, it } from 'vitest';
import StatusMark, { LOOKS } from './StatusMark.svelte';

const svgOf = (container: HTMLElement) => container.querySelector('.glyph')!;

describe('StatusMark', () => {
  it('shows each verdict as its glyph plus its word, the glyph hidden from assistive technology', () => {
    for (const verdict of ['pass', 'review', 'fail', 'no-data', 'unverified'] as const) {
      const { container, unmount } = render(StatusMark, { verdict });
      expect(container.textContent?.trim()).toBe(LOOKS[verdict].word());
      expect(container.querySelector('svg')!.getAttribute('aria-hidden')).toBe('true');
      unmount();
    }
  });

  it('keeps NO DATA and could-not-check in ink, never a verdict colour', () => {
    for (const verdict of ['no-data', 'unverified'] as const) {
      const root = render(StatusMark, { verdict, variant: 'badge' }).container.firstElementChild!;
      expect(root.className).toContain('text-ink-1');
      // ADR-0037: the status badge's muted fill (common look F31).
      expect(root.className).toContain('bg-gray-500/20');
      expect(root.className).not.toMatch(/\b(ok|caution|stop|accent)/);
    }
  });

  it('puts only the badge on a soft fill', () => {
    const plain = render(StatusMark, { verdict: 'pass' }).container.firstElementChild!;
    const badge = render(StatusMark, { verdict: 'pass', variant: 'badge' }).container
      .firstElementChild!;
    expect(plain.className).not.toContain('bg-ok-soft');
    expect(badge.className).toContain('bg-ok-soft');
  });

  it('draws the glyph in once when the verdict arrives live, even on first render', () => {
    const { container } = render(StatusMark, { verdict: 'pass', live: true });
    flushSync();
    expect(svgOf(container).classList.contains('drawing')).toBe(true);
  });

  it('does not draw a verdict loaded from a record', () => {
    const { container } = render(StatusMark, { verdict: 'pass' });
    flushSync();
    expect(svgOf(container).classList.contains('drawing')).toBe(false);
  });

  it('draws again when a live verdict changes', async () => {
    const { container, rerender } = render(StatusMark, { verdict: 'review', live: true });
    flushSync();
    svgOf(container).dispatchEvent(new Event('animationend'));
    flushSync();
    expect(svgOf(container).classList.contains('drawing')).toBe(false);
    await rerender({ verdict: 'pass', live: true });
    flushSync();
    expect(svgOf(container).classList.contains('drawing')).toBe(true);
  });
});
