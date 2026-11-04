import { fireEvent, render } from '@testing-library/svelte';
import { createRawSnippet, tick } from 'svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ELAPSED_AFTER, loadingPhase, RING_AFTER } from './action-loading.svelte';
import Button from './Button.svelte';
import ButtonGroup from './ButtonGroup.svelte';
import IconButton from './IconButton.svelte';
import Kbd from './Kbd.svelte';
import { ariaShortcut, keycap } from './keycap';
import Link from './Link.svelte';

const text = (value: string) => createRawSnippet(() => ({ render: () => `<span>${value}</span>` }));

// jsdom has no Web Animations API, which the ring's fade-in runs on: finish each animation at once.
function stubAnimate() {
  Element.prototype.animate = function () {
    const animation = { onfinish: null as null | (() => void), cancel() {}, playState: 'finished' };
    queueMicrotask(() => animation.onfinish?.());
    return animation as unknown as Animation;
  };
}

describe('loadingPhase', () => {
  it('waits 300 ms before the ring, and adds the elapsed time at 10 s', () => {
    expect(loadingPhase(null)).toBe('idle');
    expect(loadingPhase(0)).toBe('waiting');
    expect(loadingPhase(RING_AFTER - 1)).toBe('waiting');
    expect(loadingPhase(RING_AFTER)).toBe('ring');
    expect(loadingPhase(ELAPSED_AFTER - 1)).toBe('ring');
    expect(loadingPhase(ELAPSED_AFTER)).toBe('timed');
  });
});

describe('keycap', () => {
  it('prints the platform legend and names symbols for screen readers', () => {
    expect(keycap('mod', true)).toEqual({ legend: '⌘', spoken: 'Command' });
    expect(keycap('mod', false)).toEqual({ legend: 'Ctrl' });
    expect(keycap('Enter', false)).toEqual({ legend: '↵', spoken: 'Enter' });
  });

  it('shows other keys as given, single letters in capitals', () => {
    expect(keycap('k', true)).toEqual({ legend: 'K' });
    expect(keycap('/', false)).toEqual({ legend: '/' });
    expect(keycap('F2', false)).toEqual({ legend: 'F2' });
  });

  it('spells the same combination for aria-keyshortcuts', () => {
    expect(ariaShortcut(['mod', 'k'], true)).toBe('Meta+K');
    expect(ariaShortcut(['mod', 'k'], false)).toBe('Control+K');
    expect(ariaShortcut(['shift', 'enter'], false)).toBe('Shift+Enter');
    expect(ariaShortcut(['esc'], true)).toBe('Escape');
  });
});

describe('Button', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    stubAnimate();
  });
  afterEach(() => {
    vi.useRealTimers();
    Reflect.deleteProperty(Element.prototype, 'animate');
  });

  it('stays focusable when disabled with a reason, says why, and ignores presses', async () => {
    const onclick = vi.fn();
    const { getByRole } = render(Button, {
      children: text('Export'),
      disabled: true,
      reason: 'Nothing to export yet',
      onclick,
    });
    const button = getByRole('button', { name: 'Export' });
    expect(button.hasAttribute('disabled')).toBe(false);
    expect(button.getAttribute('aria-disabled')).toBe('true');
    const description = document.getElementById(button.getAttribute('aria-describedby')!);
    expect(description?.textContent).toBe('Nothing to export yet');
    await fireEvent.click(button);
    expect(onclick).not.toHaveBeenCalled();
  });

  it('is natively disabled, out of the tab order, without a reason', () => {
    const { getByRole } = render(Button, { children: text('Export'), disabled: true });
    expect(getByRole('button').hasAttribute('disabled')).toBe(true);
  });

  it('keeps the label while loading and shows the ring only after 300 ms', async () => {
    const onclick = vi.fn();
    const { getByRole, container } = render(Button, {
      children: text('Save'),
      loading: true,
      onclick,
    });
    const button = getByRole('button', { name: 'Save' });
    expect(button.getAttribute('aria-busy')).toBe('true');
    // Before the ring, the label holds the ring's room, so the width never changes.
    expect(container.querySelector('[data-reserve]')).not.toBeNull();
    expect(container.querySelector('circle')).toBeNull();

    vi.advanceTimersByTime(RING_AFTER);
    await tick();
    expect(container.querySelectorAll('circle')).toHaveLength(6);
    expect(container.querySelector('[data-reserve]')).toBeNull();
    expect(button.textContent).toContain('Save');

    await fireEvent.click(button);
    expect(onclick).not.toHaveBeenCalled();
  });

  it('puts the elapsed time in the tooltip, never in the button', async () => {
    const { getByRole } = render(Button, { children: text('Save'), loading: true });
    const button = getByRole('button');
    const before = button.textContent;
    vi.advanceTimersByTime(ELAPSED_AFTER + 2000);
    await tick();
    expect(button.textContent).toBe(before);
  });

  it('defaults to secondary and marks a decision for the ink fill', () => {
    const plain = render(Button, { children: text('Save draft') });
    expect(plain.getByRole('button').dataset.variant).toBe('secondary');
    const decision = render(Button, { children: text('Apply changes'), variant: 'decision' });
    expect(decision.getByRole('button', { name: 'Apply changes' }).dataset.variant).toBe(
      'decision',
    );
  });

  it('shows a shortcut as key caps and announces it once, through aria-keyshortcuts', () => {
    const { getByRole, container } = render(Button, {
      children: text('Run R2'),
      variant: 'primary',
      shortcut: ['mod', 'enter'],
    });
    const button = getByRole('button', { name: 'Run R2' });
    expect(button.getAttribute('aria-keyshortcuts')).toBe('Control+Enter');
    const caps = container.querySelector('kbd');
    expect(caps?.getAttribute('aria-hidden')).toBe('true');
    expect([...caps!.querySelectorAll('kbd')].map((cap) => cap.textContent?.trim())).toEqual([
      'Ctrl',
      '↵Enter',
    ]);
  });

  it('is a toggle when pressed is passed', () => {
    const { getByRole } = render(Button, { children: text('Wrap lines'), pressed: true });
    expect(getByRole('button', { pressed: true }).getAttribute('aria-pressed')).toBe('true');
  });
});

describe('IconButton', () => {
  it('takes its accessible name from the required label; the glyph is hidden', () => {
    const { getByRole } = render(IconButton, { icon: 'copy', label: 'Copy case id' });
    const button = getByRole('button', { name: 'Copy case id' });
    expect(button.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
  });

  it('announces its shortcut and keeps the caps out of the button', () => {
    const { getByRole } = render(IconButton, {
      icon: 'command',
      label: 'Command palette',
      shortcut: ['mod', 'k'],
    });
    const button = getByRole('button', { name: 'Command palette' });
    expect(button.getAttribute('aria-keyshortcuts')).toBe('Control+K');
    expect(button.querySelector('kbd')).toBeNull();
  });
});

describe('Kbd', () => {
  it('nests a keycap per key and reads the combination with plus', () => {
    // jsdom reports no platform, so these are the non-Apple legends.
    const { container } = render(Kbd, { keys: ['mod', 'k'] });
    const caps = container.querySelectorAll('kbd kbd');
    expect([...caps].map((cap) => cap.textContent?.trim())).toEqual(['Ctrl', 'K']);
    expect(container.querySelector('.sr-only')?.textContent).toBe('+');
  });
});

describe('ButtonGroup and Link', () => {
  it('names the group for assistive technology', () => {
    const { getByRole } = render(ButtonGroup, { label: 'Export', children: text('') });
    expect(getByRole('group', { name: 'Export' })).not.toBeNull();
  });

  it('speaks the external arrow only when given words for it', () => {
    const plain = render(Link, {
      href: 'https://example.org/notes',
      external: true,
      children: text('Notes'),
    });
    expect(plain.getByRole('link').querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
    const spoken = render(Link, {
      href: 'https://example.org/guide',
      external: true,
      externalLabel: 'leaves 4CE',
      children: text('Guide'),
    });
    expect(spoken.getByRole('link', { name: /^Guide\sleaves 4CE$/ })).not.toBeNull();
  });

  it('gives an in-app path the base path and leaves client routing on', () => {
    const { getByRole } = render(Link, { href: '/ui#actions', children: text('Actions') });
    const link = getByRole('link', { name: 'Actions' });
    expect(link.getAttribute('href')).toBe('/ui#actions');
    expect(link.hasAttribute('rel')).toBe(false);
  });
});
