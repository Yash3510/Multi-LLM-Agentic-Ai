import { render } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import { describe, expect, it } from 'vitest';
import GroupHeading, { groupLabel } from './GroupHeading.svelte';
import ListRow from './ListRow.svelte';
import SortHeader from './SortHeader.svelte';

const text = (value: string) => createRawSnippet(() => ({ render: () => `<span>${value}</span>` }));

describe('GroupHeading', () => {
  it('names the fixed bands from messages and months and years from Intl', () => {
    expect(groupLabel({ band: 'today' }, 'en-IN')).toBe('Today');
    expect(groupLabel({ band: 'week' }, 'en-IN')).toBe('Previous 7 days');
    expect(groupLabel({ band: 'month-name', month: 9 }, 'en-IN')).toBe('October');
    expect(groupLabel({ band: 'month-name', month: 9 }, 'hi-IN')).toBe('अक्टूबर');
    // A year is a name, not an amount: never grouped as "2,025".
    expect(groupLabel({ band: 'year', year: 2025 }, 'en-IN')).toBe('2025');
  });

  it('is a heading, so a screen reader can jump between groups', () => {
    const { getByRole } = render(GroupHeading, { group: { band: 'yesterday' } });
    expect(getByRole('heading', { name: 'Yesterday' })).toBeTruthy();
  });
});

describe('SortHeader', () => {
  it('states the sort on the column header and keeps the button a plain label', () => {
    const sort = { column: 'title', direction: 'descending' } as const;
    const { getByRole } = render(SortHeader, {
      column: 'title',
      label: 'Title',
      sort,
      onsort: () => {},
    });
    expect(getByRole('columnheader').getAttribute('aria-sort')).toBe('descending');
    expect(getByRole('button', { name: 'Title' })).toBeTruthy();
  });

  it('reserves the caret on an unsorted column so the labels stay aligned', () => {
    const { container } = render(SortHeader, {
      column: 'updated',
      label: 'Updated',
      sort: { column: 'title', direction: 'ascending' },
      onsort: () => {},
    });
    expect(container.querySelector('[role="columnheader"]')?.getAttribute('aria-sort')).toBe(
      'none',
    );
    expect(container.querySelector('[data-caret]')?.getAttribute('data-hidden')).toBe('');
  });
});

describe('ListRow', () => {
  it('is a link when it opens something, and marks the open one as current', () => {
    const { getByRole } = render(ListRow, { href: '/ui', current: true, children: text('R2') });
    const link = getByRole('link', { name: 'R2' });
    expect(link.getAttribute('aria-current')).toBe('page');
  });

  it('is a plain row otherwise, never a button around other controls', () => {
    const { container } = render(ListRow, { children: text('R3') });
    const row = container.querySelector('[data-list-row]')!;
    expect(row.tagName).toBe('DIV');
    expect(row.hasAttribute('aria-current')).toBe(false);
  });
});
