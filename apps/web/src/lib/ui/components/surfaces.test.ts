import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { createRawSnippet, tick } from 'svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Card from './Card.svelte';
import Harness from './SurfacesHarness.test.svelte';
import Tabs from './Tabs.svelte';

const text = (value: string) => createRawSnippet(() => ({ render: () => `<span>${value}</span>` }));

// jsdom has no Web Animations API, which Svelte transitions run on: finish each animation at once.
function stubAnimate() {
  Element.prototype.animate = function () {
    const animation = { onfinish: null as null | (() => void), cancel() {}, playState: 'finished' };
    queueMicrotask(() => animation.onfinish?.());
    return animation as unknown as Animation;
  };
}

beforeEach(stubAnimate);
afterEach(() => Reflect.deleteProperty(Element.prototype, 'animate'));

describe('Card', () => {
  it('is one link when it has an href, and current when selected', () => {
    const { getByRole } = render(Card, {
      href: '/ui',
      selected: true,
      children: text('CASE-0142'),
    });
    const link = getByRole('link', { name: 'CASE-0142' });
    expect(link.getAttribute('href')).toBe('/ui');
    expect(link.getAttribute('aria-current')).toBe('true');
    expect(link.dataset.surface).toBe('card');
  });

  it('goes nowhere when disabled, and says why while staying focusable', () => {
    const { getByRole } = render(Card, {
      href: '/ui',
      disabled: true,
      reason: 'Waiting for R2 to finish',
      children: text('CASE-0142'),
    });
    const link = getByRole('link');
    expect(link.hasAttribute('href')).toBe(false);
    expect(link.getAttribute('aria-disabled')).toBe('true');
    expect(link.getAttribute('tabindex')).toBe('0');
    const reason = document.getElementById(link.getAttribute('aria-describedby')!);
    expect(reason?.textContent).toBe('Waiting for R2 to finish');
  });

  it('is a toggle button only when it can be selected, and ignores presses while loading', async () => {
    const onclick = vi.fn();
    const plain = render(Card, { onclick, children: text('R2') });
    expect(plain.getByRole('button').hasAttribute('aria-pressed')).toBe(false);
    plain.unmount();

    const { getByRole } = render(Card, {
      onclick,
      selected: false,
      loading: true,
      children: text('R2'),
    });
    const button = getByRole('button', { name: 'R2' });
    expect(button.getAttribute('aria-pressed')).toBe('false');
    expect(button.getAttribute('aria-busy')).toBe('true');
    await fireEvent.click(button);
    expect(onclick).not.toHaveBeenCalled();
  });
});

describe('Dialog', () => {
  it('moves focus in, closes on Esc and hands focus back to its opener', async () => {
    const { getByRole } = render(Harness, { kind: 'dialog' });
    const opener = getByRole('button', { name: 'Rename case' });
    opener.focus();
    await fireEvent.click(opener);
    const dialog = await waitFor(() => getByRole('dialog', { name: 'Rename CASE-0142' }));
    await waitFor(() => expect(document.activeElement?.hasAttribute('data-autofocus')).toBe(true));
    expect(dialog.getAttribute('aria-modal')).toBe('true');

    await fireEvent.keyDown(document.activeElement!, { key: 'Escape' });
    await waitFor(() => expect(document.querySelector('[role="dialog"]')).toBeNull());
    await waitFor(() => expect(document.activeElement).toBe(opener));
  });

  it('starts a confirmation on the dismiss and ignores Enter', async () => {
    const onconfirm = vi.fn();
    const { getByRole } = render(Harness, { kind: 'confirm', onconfirm });
    await fireEvent.click(getByRole('button', { name: 'Delete drafts' }));
    const dialog = await waitFor(() => getByRole('alertdialog', { name: 'Delete 3 drafts?' }));
    expect(dialog.getAttribute('aria-describedby')).toBeTruthy();
    await waitFor(() => expect(document.activeElement?.textContent).toBe('Keep drafts'));
    // No close button: the dismiss is the way out, besides Esc.
    expect(dialog.querySelector('[aria-label="Close"]')).toBeNull();

    const confirm = getByRole('button', { name: 'Delete 3 drafts' });
    confirm.focus();
    const enter = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true });
    confirm.dispatchEvent(enter);
    expect(enter.defaultPrevented).toBe(true);
  });
});

describe('SidePanel', () => {
  it('opens beside the page, takes focus to its title, and hands it back on Esc', async () => {
    const { getByRole, queryByRole } = render(Harness, { kind: 'dock' });
    const opener = getByRole('button', { name: 'Open CASE-0142' });
    opener.focus();
    await fireEvent.click(opener);
    const panel = getByRole('complementary', { name: 'CASE-0142' });
    await waitFor(() => expect(document.activeElement?.textContent?.trim()).toBe('CASE-0142'));
    // Not modal: no aria-modal and the page keeps its controls.
    expect(panel.hasAttribute('aria-modal')).toBe(false);
    expect(getByRole('button', { name: 'Another page control' })).toBeTruthy();

    await fireEvent.keyDown(document.activeElement!, { key: 'Escape' });
    await tick();
    expect(document.activeElement).toBe(opener);
    await waitFor(() => expect(queryByRole('complementary')).toBeNull());
  });
});

describe('Disclosure', () => {
  it('keeps the region mounted for the grid-rows animation and reports its state', async () => {
    const { getByRole, container } = render(Harness, { kind: 'disclosure' });
    const trigger = getByRole('button', { name: /Show the inputs/ });
    const region = container.querySelector<HTMLElement>('[data-expand]')!;
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    expect(region.dataset.state).toBe('closed');
    expect(region.hidden).toBe(false);

    await fireEvent.click(trigger);
    expect(trigger.getAttribute('aria-expanded')).toBe('true');
    expect(region.dataset.state).toBe('open');
  });
});

describe('Tabs', () => {
  it('marks the current tab and puts its count in its name', () => {
    const { getByRole } = render(Tabs, {
      label: 'Case views',
      value: 'rules',
      tabs: [
        { value: 'overview', label: 'Overview' },
        { value: 'rules', label: 'Rules', count: 12 },
      ],
      panel: createRawSnippet(() => ({ render: () => '<p>Panel</p>' })),
    });
    expect(getByRole('tablist', { name: 'Case views' })).toBeTruthy();
    const current = getByRole('tab', { name: 'Rules 12' });
    expect(current.getAttribute('aria-selected')).toBe('true');
    expect(getByRole('tab', { name: 'Overview' }).getAttribute('aria-selected')).toBe('false');
  });
});
