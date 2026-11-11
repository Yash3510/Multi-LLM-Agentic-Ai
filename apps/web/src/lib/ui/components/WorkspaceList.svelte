<script lang="ts" module>
  export interface ListFilter {
    id: string;
    /** What the trigger says now. */
    label: string;
    value: string;
    options: { value: string; label: string }[];
    onChange: (value: string) => void;
    /** The view filter's label box is 5 px wider than its text, which sets the caret apart. */
    padded?: boolean;
    caret?: number;
    /** Once something is chosen an x clears it, in place of the caret (look §2.1 tag filter). */
    clearable?: boolean;
  }
</script>

<script lang="ts">
  // A workspace tab's list frame (workspace look §2, §4.1 to §4.3, §6.1): search, the filters,
  // the sortable Title and Updated at header, the rows, and the empty message.
  import type { Snippet } from 'svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Menu from './Menu.svelte';

  type Props = {
    searchLabel: string;
    query: string;
    filters: ListFilter[];
    sort: { by: 'name' | 'updated'; down: boolean };
    /** How many rows show; none shows the empty message. */
    count: number;
    emptyTitle: string;
    rows: Snippet;
  };

  let {
    searchLabel,
    query = $bindable(),
    filters,
    sort = $bindable(),
    count,
    emptyTitle,
    rows,
  }: Props = $props();

  // A column turns its order around when pressed again; a new column starts descending (F59).
  function order(by: 'name' | 'updated') {
    sort = { by, down: sort.by === by ? !sort.down : true };
  }
</script>

<div class="screen">
  <div class="toolbar">
    <label class="search">
      <span class="search-icon"><Icon name="magnifying-glass" size={14} /></span>
      <input bind:value={query} placeholder={searchLabel} aria-label={searchLabel} />
      {#if query}
        <button type="button" class="clear" aria-label="Clear search" onclick={() => (query = '')}>
          <Icon name="tools-failed" size={12} />
        </button>
      {/if}
    </label>
    <div class="filters">
      {#each filters as filter (filter.id)}
        <Menu
          label={filter.label}
          backLabel="Back"
          align="end"
          items={[
            {
              type: 'choices',
              id: filter.id,
              label: filter.label,
              value: filter.value,
              options: filter.options,
              onChange: filter.onChange,
            },
          ]}
        >
          {#snippet trigger({ props })}
            <button {...props} class="filter"
              ><span class:view-label={filter.padded}>{filter.label}</span
              >{#if filter.clearable && filter.value}<span
                  class="clear-choice"
                  role="button"
                  tabindex="-1"
                  aria-label="Clear"
                  onpointerdown={(event) => {
                    event.stopPropagation();
                    event.preventDefault();
                    filter.onChange('');
                  }}><Icon name="x" size={14} /></span
                >{:else}<Icon name="caret-down" size={filter.caret ?? 9} />{/if}</button
            >
          {/snippet}
        </Menu>
      {/each}
    </div>
  </div>

  {#if count}
    <div class="list">
      <div class="head">
        <button type="button" class="col-title" onclick={() => order('name')}>
          Title
          {#if sort.by === 'name'}<Icon
              name={sort.down ? 'caret-down' : 'caret-up'}
              size={8}
            />{/if}
        </button>
        <button type="button" class="col-updated" onclick={() => order('updated')}>
          Updated at
          {#if sort.by === 'updated'}<Icon
              name={sort.down ? 'caret-down' : 'caret-up'}
              size={8}
            />{/if}
        </button>
      </div>
      <div class="rows">{@render rows()}</div>
    </div>
  {:else}
    <div class="empty">
      <div class="empty-inner">
        <p class="empty-title">{emptyTitle}</p>
        <p class="empty-help">
          Try adjusting your search or filter to find what you are looking for.
        </p>
      </div>
    </div>
  {/if}
</div>

<style>
  .screen {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-inline: 12px;
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    block-size: 32px;
  }

  .search {
    display: flex;
    flex: 1;
    align-items: center;
    min-inline-size: 0;
    color: var(--color-gray-700);
    border-radius: var(--radius-pill);
    padding-inline: 12px;
    background-image: var(--field-inset-fill);
    box-shadow: var(--field-inset-edge);
  }

  .search-icon {
    display: inline-flex;
    margin-inline: 4px 12px;
  }

  .search input {
    inline-size: 100%;
    padding-block: 4px;
    border-radius: 0 12px 12px 0;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .search input::placeholder {
    color: var(--color-gray-400);
  }

  .search input:focus {
    outline: none;
  }

  .clear {
    display: grid;
    place-items: center;
    margin-inline-start: 6px;
    padding: 2px;
    border-radius: var(--radius-pill);
  }

  .clear:hover {
    background-color: var(--color-gray-100);
  }

  /* Knowledge and Prompts cap the filters at 55 % of the row, 2 px apart (look §4.1, §6.1). */
  .filters {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 2px;
    max-inline-size: 55%;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .clear-choice {
    display: inline-flex;
  }

  .view-label {
    padding-inline-end: 5px;
  }

  .filter {
    display: flex;
    align-items: center;
    gap: 2px;
    block-size: 32px;
    padding: 6px;
    border-radius: var(--radius-inset);
    color: var(--color-gray-700);
    font-size: var(--text-small);
    /* The running app keeps the 14 px line ratio at 13 px: 18.57 px lines. */
    line-height: calc(20 / 14);
    white-space: nowrap;
    transition: color 150ms;
  }

  .filter:hover {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) :is(.search, .filter) {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .filter:hover {
    color: var(--color-gray-100);
  }

  .list {
    margin-block-end: 4px;
  }

  .head {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    padding: 0 6px 2px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  :global([data-theme='dark']) .head {
    color: var(--color-gray-600);
  }

  .col-title,
  .col-updated {
    display: flex;
    align-items: center;
    gap: 4px;
    padding-block: 2px;
  }

  .col-title {
    flex: 1;
    min-inline-size: 0;
    text-align: start;
  }

  .col-updated {
    flex-shrink: 0;
    justify-content: flex-end;
    inline-size: 144px;
    text-align: end;
  }

  .rows {
    display: grid;
    gap: 2px;
  }

  .empty {
    display: flex;
    justify-content: center;
    padding: 64px 0 96px;
  }

  .empty-inner {
    max-inline-size: 384px;
    color: var(--color-gray-900);
    text-align: center;
  }

  :global([data-theme='dark']) .empty-inner {
    color: var(--color-gray-100);
  }

  .empty-title {
    margin-block-end: 6px;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .empty-help {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 20px;
  }

  :is(.filter, .clear, .col-title, .col-updated):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
