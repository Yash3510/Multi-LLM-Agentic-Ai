// A list's sort: one column at a time. Pressing the sorted column flips it; pressing another
// column starts that column at its own first direction (dates newest first, names A to Z).
export type SortDirection = 'ascending' | 'descending';

export interface Sort {
  column: string;
  direction: SortDirection;
}

export function nextSort(sort: Sort, column: string, first: SortDirection = 'ascending'): Sort {
  if (sort.column !== column) return { column, direction: first };
  return { column, direction: sort.direction === 'ascending' ? 'descending' : 'ascending' };
}

/** The `aria-sort` value for a column header: only the sorted column names a direction. */
export function ariaSort(sort: Sort, column: string): SortDirection | 'none' {
  return sort.column === column ? sort.direction : 'none';
}
