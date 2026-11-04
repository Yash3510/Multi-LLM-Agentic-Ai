import { describe, expect, it } from 'vitest';
import { ariaSort, nextSort } from './sort';

describe('nextSort', () => {
  it('flips the direction when the active column is pressed again', () => {
    expect(nextSort({ column: 'title', direction: 'ascending' }, 'title')).toEqual({
      column: 'title',
      direction: 'descending',
    });
    expect(nextSort({ column: 'title', direction: 'descending' }, 'title')).toEqual({
      column: 'title',
      direction: 'ascending',
    });
  });

  it("starts a new column at that column's first direction", () => {
    const sort = { column: 'title', direction: 'ascending' } as const;
    expect(nextSort(sort, 'updated', 'descending')).toEqual({
      column: 'updated',
      direction: 'descending',
    });
    expect(nextSort(sort, 'owner')).toEqual({ column: 'owner', direction: 'ascending' });
  });
});

describe('ariaSort', () => {
  it('names the direction on the sorted column only', () => {
    const sort = { column: 'title', direction: 'descending' } as const;
    expect(ariaSort(sort, 'title')).toBe('descending');
    expect(ariaSort(sort, 'updated')).toBe('none');
  });
});
