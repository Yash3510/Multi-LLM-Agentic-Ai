import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { graceClose, GRACE_MS } from './hover-intent';
import { drillHint, flatRows, hasIcons, levelAt, validPath, type MenuEntry } from './menu-model';

const choose = vi.fn();

const ITEMS: MenuEntry[] = [
  {
    type: 'group',
    id: 'case',
    label: 'Case',
    items: [
      { id: 'open', label: 'Open CASE-0142', icon: 'arrow-up-right' },
      { id: 'copy', label: 'Copy case id', shortcut: ['mod', 'c'] },
    ],
  },
  { type: 'separator' },
  {
    type: 'drill',
    id: 'density',
    label: 'Density',
    items: [
      {
        type: 'choices',
        id: 'density-choice',
        label: 'Density',
        value: 'default',
        options: [
          { value: 'comfortable', label: 'Comfortable' },
          { value: 'default', label: 'Default' },
        ],
        onChange: choose,
      },
    ],
  },
  {
    type: 'drill',
    id: 'export',
    label: 'Export as',
    items: [
      {
        type: 'drill',
        id: 'sheet',
        label: 'Spreadsheet',
        items: [{ id: 'csv', label: 'CSV' }],
      },
    ],
  },
  { type: 'drill', id: 'locked', label: 'Locked', disabled: true, items: [] },
];

describe('levelAt', () => {
  it('shows the top level for an empty path', () => {
    const level = levelAt(ITEMS, []);
    expect(level.entries).toBe(ITEMS);
    expect(level.trail).toEqual([]);
  });

  it('follows drill ids down, keeping the trail for the back row', () => {
    const level = levelAt(ITEMS, ['export', 'sheet']);
    expect(level.trail.map((drill) => drill.label)).toEqual(['Export as', 'Spreadsheet']);
    expect(level.entries).toEqual([{ id: 'csv', label: 'CSV' }]);
  });

  it('stops at the deepest valid level when the path has gone stale', () => {
    expect(levelAt(ITEMS, ['export', 'gone']).trail.map((drill) => drill.id)).toEqual(['export']);
    expect(validPath(ITEMS, ['density', 'gone', 'deeper'])).toEqual(['density']);
  });

  it('never enters a disabled drill row', () => {
    expect(levelAt(ITEMS, ['locked']).trail).toEqual([]);
  });

  it('finds drill rows inside groups', () => {
    const grouped: MenuEntry[] = [
      { type: 'group', id: 'g', label: 'G', items: [ITEMS[2] as never] },
    ];
    expect(levelAt(grouped, ['density']).trail).toHaveLength(1);
  });
});

describe('menu rows', () => {
  it('names the current choice at the end of its drill row', () => {
    expect(drillHint(ITEMS[2] as never)).toBe('Default');
    expect(drillHint(ITEMS[3] as never)).toBeUndefined();
  });

  it('opens groups up in order', () => {
    expect(flatRows(ITEMS).map((entry) => ('id' in entry ? entry.id : entry.type))).toEqual([
      'open',
      'copy',
      'separator',
      'density',
      'export',
      'locked',
    ]);
  });

  it('keeps an icon column only where some row has an icon', () => {
    expect(hasIcons(ITEMS)).toBe(true);
    expect(hasIcons(levelAt(ITEMS, ['density']).entries)).toBe(false);
  });
});

describe('graceClose', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('opens at once and waits out the grace before closing', () => {
    const set = vi.fn();
    const grace = graceClose(set);
    grace.request(true);
    expect(set).toHaveBeenLastCalledWith(true);
    grace.request(false);
    vi.advanceTimersByTime(GRACE_MS - 1);
    expect(set).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(1);
    expect(set).toHaveBeenLastCalledWith(false);
  });

  it('stays open when the pointer comes back within the grace', () => {
    const set = vi.fn();
    const grace = graceClose(set);
    grace.request(true);
    grace.request(false);
    vi.advanceTimersByTime(GRACE_MS / 2);
    grace.request(true);
    vi.advanceTimersByTime(GRACE_MS * 2);
    expect(set).not.toHaveBeenCalledWith(false);
  });

  it('closes at once after a key, a blur or a press', () => {
    const set = vi.fn();
    const grace = graceClose(set);
    grace.request(true);
    grace.immediate();
    grace.request(false);
    expect(set).toHaveBeenLastCalledWith(false);
    // The next close waits again.
    grace.request(true);
    grace.request(false);
    expect(set).toHaveBeenLastCalledWith(true);
  });

  it('drops a pending close when cancelled', () => {
    const set = vi.fn();
    const grace = graceClose(set);
    grace.request(false);
    grace.cancel();
    vi.advanceTimersByTime(GRACE_MS * 2);
    expect(set).not.toHaveBeenCalled();
  });
});
