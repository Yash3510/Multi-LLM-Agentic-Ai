import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Logomark from './Logomark.svelte';
import Sidebar from './Sidebar.svelte';
import TopBar from './TopBar.svelte';
import { SIDEBAR_WIDTH, sidebarWidth } from './sidebar-width';

const DESTINATIONS = [
  { href: '/ui', label: 'Notes', icon: 'note' },
  { href: '/ui#lists', label: 'Workspace', icon: 'workspace' },
] as const;

const props = (open: boolean) => ({
  open,
  productName: '4CE',
  userName: 'Asha Rao',
  destinations: [...DESTINATIONS],
  current: '/ui',
});

describe('sidebarWidth', () => {
  it('keeps a stored width inside 220 to 480 px and falls back to 245', () => {
    expect(SIDEBAR_WIDTH).toEqual({ min: 220, max: 480, initial: 245 });
    expect(sidebarWidth(300)).toBe(300);
    expect(sidebarWidth(100)).toBe(220);
    expect(sidebarWidth(900)).toBe(480);
    expect(sidebarWidth(Number.NaN)).toBe(245);
    expect(sidebarWidth(undefined)).toBe(245);
    expect(sidebarWidth('312')).toBe(312);
  });
});

describe('Sidebar', () => {
  it('lists New Chat, Search and the destinations, and marks the current one', () => {
    const { getByRole } = render(Sidebar, props(true));
    expect(getByRole('button', { name: 'New Chat' })).toBeTruthy();
    expect(getByRole('button', { name: 'Search' })).toBeTruthy();
    expect(getByRole('link', { name: 'Notes' }).getAttribute('aria-current')).toBe('page');
    expect(getByRole('link', { name: 'Workspace' }).hasAttribute('aria-current')).toBe(false);
  });

  it('keeps a destination current on the pages under it, as the running app does', () => {
    const { getByRole } = render(Sidebar, { ...props(false), current: '/ui/lists/create' });
    expect(getByRole('link', { name: 'Notes' }).getAttribute('aria-current')).toBe('page');
  });

  it('closes to the rail, which keeps every action reachable by name', async () => {
    const { getByRole, component } = render(Sidebar, props(true));
    await fireEvent.click(getByRole('button', { name: 'Close Sidebar' }));
    expect(component.isOpen()).toBe(false);
    expect(getByRole('button', { name: 'Open Sidebar' })).toBeTruthy();
    expect(getByRole('button', { name: 'New Chat' })).toBeTruthy();
    expect(getByRole('link', { name: 'Notes' })).toBeTruthy();
  });

  it('is a labelled navigation landmark', () => {
    const { getByRole } = render(Sidebar, props(false));
    expect(getByRole('navigation', { name: 'Main' })).toBeTruthy();
  });
});

describe('TopBar', () => {
  it('falls back to New Chat and offers chat actions only for a saved chat', () => {
    const blank = render(TopBar, {});
    expect(blank.getByText('New Chat')).toBeTruthy();
    expect(blank.queryByRole('button', { name: 'Chat actions' })).toBeNull();
    blank.unmount();

    const saved = render(TopBar, { title: 'R2 · Ratio check', onchatactions: () => {} });
    expect(saved.getByText('R2 · Ratio check')).toBeTruthy();
    expect(saved.getByRole('button', { name: 'Chat actions' })).toBeTruthy();
  });
});

describe('Logomark', () => {
  it('ships the ink mark for light and the white mark for dark, unchanged files, decorative', () => {
    const { container } = render(Logomark, { size: 22 });
    const [ink, white] = [...container.querySelectorAll('img')];
    // Small SVGs are inlined as data URLs; each still carries its own file's fill, read from the
    // brand file itself rather than restated here.
    const source = (img: HTMLImageElement) => decodeURIComponent(img.getAttribute('src') ?? '');
    const fill = (file: string) =>
      readFileSync(join(import.meta.dirname, '../brand', file), 'utf8').match(/fill="([^"]+)"/)![1];
    expect(source(ink)).toContain(`fill='${fill('4ce-logomark-ink.svg')}'`);
    expect(source(white)).toContain(`fill='${fill('4ce-logomark-white.svg')}'`);
    expect([ink.dataset.theme, white.dataset.theme]).toEqual(['light', 'dark']);
    for (const img of [ink, white]) {
      expect(img.getAttribute('alt')).toBe('');
      expect(img.getAttribute('width')).toBe('22');
    }
  });
});
