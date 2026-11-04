import { render } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Badge, { countText } from './Badge.svelte';
import InlineAlert from './InlineAlert.svelte';
import Skeleton, { lineWidths } from './Skeleton.svelte';
import Tag, { fileType } from './Tag.svelte';
import WorkingDots, { DOTS } from './WorkingDots.svelte';

const text = (value: string) => createRawSnippet(() => ({ render: () => `<span>${value}</span>` }));

describe('Badge', () => {
  it('groups in the locale and caps past max', () => {
    expect(countText(123456, 999999, 'en-IN')).toBe('1,23,456');
    expect(countText(100, 99, 'en-IN')).toBe('99+');
    expect(countText(-3, 99, 'en-IN')).toBe('0');
  });

  it('gives assistive technology the whole meaning instead of the bare figure', () => {
    const { container } = render(Badge, { count: 2, label: '2 waiting for sign-off' });
    expect(container.querySelector('[aria-hidden="true"]')?.textContent).toBe('2');
    expect(container.querySelector('.sr-only')?.textContent).toBe('2 waiting for sign-off');
  });

  // ADR-0037 amendment: a sky count for what waits on a person.
  it('draws a count that waits on a person in sky, never a verdict hue', () => {
    const badge = render(Badge, { count: 2, tone: 'ink' }).container.firstElementChild!;
    expect(badge.className).toContain('bg-sky-500/10');
    expect(badge.className).toContain('text-sky-700');
    expect(badge.className).not.toMatch(/\b(ok|caution|stop)/);
  });
});

describe('Tag', () => {
  it('shows a file type as its extension with the matching glyph', () => {
    expect(fileType('ratios.XLSX')).toEqual({ label: 'XLSX', icon: 'file-xls' });
    expect(fileType('brief.docx')).toEqual({ label: 'DOCX', icon: 'file-doc' });
    expect(fileType('summary.pdf')).toEqual({ label: 'PDF', icon: 'file-text' });
    expect(fileType('pptx')).toEqual({ label: 'PPTX', icon: 'file-ppt' });
  });

  it('never borrows a verdict or accent colour', () => {
    const tag = render(Tag, { file: 'export.csv' }).container.firstElementChild!;
    expect(tag.textContent?.trim()).toBe('CSV');
    expect(tag.className).not.toMatch(/\b(ok|caution|stop|accent)/);
  });

  // ADR-0037 amendment: the 7 px tag on the faint track.
  it('takes the tag radius on the faint track, never a pill', () => {
    const tag = render(Tag, { label: 'Draft' }).container.firstElementChild!;
    expect(tag.className).toContain('rounded-tag');
    expect(tag.className).toContain('bg-track');
    expect(tag.className).not.toContain('rounded-pill');
  });
});

describe('WorkingDots', () => {
  it('puts six dots on the corners of a pointy-top hexagon inside the 14 px box', () => {
    expect(DOTS).toHaveLength(6);
    expect(DOTS[0]).toEqual([7, 2]);
    for (const [x, y] of DOTS) expect(Math.hypot(x - 7, y - 7)).toBeCloseTo(5, 2);
  });

  it('is decorative unless labelled', () => {
    const plain = render(WorkingDots).container.querySelector('svg')!;
    expect(plain.getAttribute('aria-hidden')).toBe('true');
    const { getByRole } = render(WorkingDots, { label: 'Working' });
    expect(getByRole('img', { name: 'Working' })).toBeTruthy();
  });

  describe('with a delay', () => {
    afterEach(() => vi.useRealTimers());

    it('keeps its space but stays hidden until the delay passes', async () => {
      vi.useFakeTimers();
      const svg = render(WorkingDots, { delay: 300 }).container.querySelector('svg')!;
      expect(svg.classList.contains('waiting')).toBe(true);
      await vi.advanceTimersByTimeAsync(300);
      expect(svg.classList.contains('waiting')).toBe(false);
    });
  });
});

describe('Skeleton', () => {
  it('ends a paragraph on a short line', () => {
    expect(lineWidths(3, 60)).toEqual([100, 100, 60]);
    expect(lineWidths(0, 100)).toEqual([100]);
    expect(lineWidths(1, 400)).toEqual([100]);
  });

  it('is hidden from assistive technology and takes its type step', () => {
    const root = render(Skeleton, { lines: 2, step: 'body' }).container.firstElementChild!;
    expect(root.getAttribute('aria-hidden')).toBe('true');
    expect(root.className).toContain('text-body');
    expect(root.querySelectorAll('.bar')).toHaveLength(2);
  });
});

describe('InlineAlert', () => {
  it('makes stop an alert and the other tones polite status messages', () => {
    const stop = render(InlineAlert, { tone: 'stop', children: text('Not saved') });
    expect(stop.getByRole('alert').textContent).toContain('Not saved');
    const caution = render(InlineAlert, { tone: 'caution', children: text('Near the limit') });
    expect(caution.getByRole('status').textContent).toContain('Near the limit');
  });

  it('puts the action in a row under the text, not beside it', () => {
    const { getByRole } = render(InlineAlert, {
      tone: 'stop',
      title: 'Not saved',
      children: text('The server did not answer.'),
      action: createRawSnippet(() => ({ render: () => '<button>Retry saving</button>' })),
    });
    const button = getByRole('button', { name: 'Retry saving' });
    const message = getByRole('alert').querySelector('p')!.parentElement!;
    // The action row is the text block's next sibling inside the same column.
    expect(message.nextElementSibling?.contains(button)).toBe(true);
  });
});
