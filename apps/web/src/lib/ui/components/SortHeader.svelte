<script lang="ts">
  // A sortable column header (layout look §9.2): the label with a caret 6 px after it for the
  // sorted column's direction. Unsorted columns keep an invisible caret so the labels line up.
  // The header states the sort with aria-sort; the button is the label alone.
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { ariaSort, type Sort } from './sort';

  type Props = {
    column: string;
    label: string;
    sort: Sort;
    onsort: (column: string) => void;
    align?: 'start' | 'end';
  };

  let { column, label, sort, onsort, align = 'start' }: Props = $props();

  const state = $derived(ariaSort(sort, column));
</script>

<div role="columnheader" aria-sort={state} class="sort-header" data-align={align}>
  <button type="button" class="sort-button" onclick={() => onsort(column)}>
    {label}
    <span data-caret aria-hidden="true" data-hidden={state === 'none' ? '' : undefined}>
      <Icon name={state === 'descending' ? 'sort-caret-down' : 'caret-up'} size={12} />
    </span>
  </button>
</div>

<style>
  .sort-header {
    display: flex;
  }

  .sort-header[data-align='end'] {
    justify-content: flex-end;
  }

  .sort-button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: var(--spacing-1) 6px;
    border-radius: var(--radius-tight);
    color: var(--color-ink-3);
    font-size: var(--text-caption);
    line-height: var(--text-caption--line-height);
    user-select: none;
    transition: color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .sort-header:not([aria-sort='none']) .sort-button,
  .sort-button:hover {
    color: var(--color-ink-1);
  }

  .sort-button:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  [data-caret] {
    display: inline-flex;
  }

  [data-caret][data-hidden] {
    visibility: hidden;
  }
</style>
