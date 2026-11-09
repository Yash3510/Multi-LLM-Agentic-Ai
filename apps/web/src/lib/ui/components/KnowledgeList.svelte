<script lang="ts">
  // The Knowledge tab (workspace look §4.1 to §4.3): search, the view and source filters, the
  // sortable header and the rows. Deleting asks first.
  import type { KnowledgeBase } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import KnowledgeRow from './KnowledgeRow.svelte';
  import Menu from './Menu.svelte';

  type Props = {
    bases: KnowledgeBase[];
    /** The signed-in person's email, for "Created by you". */
    me?: string;
    admin?: boolean;
    onopen?: (id: string) => void;
    ondelete?: (id: string) => void;
  };

  let { bases, me, admin = false, onopen, ondelete }: Props = $props();

  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  let source = $state<'local' | 'connected' | undefined>();
  let sort = $state<{ by: 'name' | 'updated'; down: boolean }>({ by: 'updated', down: true });
  let deleting = $state<string>();

  const VIEWS = { all: 'All', mine: 'Created by you', shared: 'Shared with you' } as const;
  const SOURCES = { local: 'Local', connected: 'Connected' } as const;

  const shown = $derived.by(() => {
    const q = query.trim().toLowerCase();
    const list = bases.filter(
      (base) =>
        base.name.toLowerCase().includes(q) &&
        (!source || base.source === source) &&
        (view === 'all' || (view === 'mine') === (base.owner?.email === me)),
    );
    const sign = sort.down ? -1 : 1;
    return list.sort((a, b) =>
      sort.by === 'name'
        ? sign * a.name.localeCompare(b.name)
        : sign * (a.updated.getTime() - b.updated.getTime()),
    );
  });

  // A column turns its order around when pressed again; a new column starts descending (F59).
  function order(by: 'name' | 'updated') {
    sort = { by, down: sort.by === by ? !sort.down : true };
  }
</script>

<div class="screen">
  <div class="toolbar">
    <label class="search">
      <span class="search-icon"><Icon name="magnifying-glass" size={14} /></span>
      <input bind:value={query} placeholder="Search Knowledge" aria-label="Search Knowledge" />
      {#if query}
        <button type="button" class="clear" aria-label="Clear search" onclick={() => (query = '')}>
          <Icon name="tools-failed" size={12} />
        </button>
      {/if}
    </label>
    <div class="filters">
      <Menu
        label={VIEWS[view]}
        backLabel="Back"
        align="end"
        items={[
          {
            type: 'choices',
            id: 'view',
            label: 'View',
            value: view,
            options: Object.entries(VIEWS).map(([value, label]) => ({ value, label })),
            onChange: (value) => (view = value as typeof view),
          },
        ]}
      >
        {#snippet trigger({ props })}
          <button {...props} class="filter"
            ><span class="view-label">{VIEWS[view]}</span><Icon
              name="caret-down"
              size={9}
            /></button
          >
        {/snippet}
      </Menu>
      <Menu
        label="Source"
        backLabel="Back"
        align="end"
        items={[
          {
            type: 'choices',
            id: 'source',
            label: 'Source',
            value: source ?? '',
            options: [
              { value: '', label: 'All Sources' },
              ...Object.entries(SOURCES).map(([value, label]) => ({ value, label })),
            ],
            onChange: (value) => (source = (value || undefined) as typeof source),
          },
        ]}
      >
        {#snippet trigger({ props })}
          <button {...props} class="filter source"
            ><span>{source ? SOURCES[source] : 'All Sources'}</span><Icon
              name="caret-down"
              size={10}
            /></button
          >
        {/snippet}
      </Menu>
    </div>
  </div>

  {#if shown.length}
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
      <div class="rows">
        {#each shown as base (base.id)}
          <KnowledgeRow {base} {admin} {onopen} ondelete={(id) => (deleting = id)} />
        {/each}
      </div>
    </div>
  {:else}
    <div class="empty">
      <div class="empty-inner">
        <p class="empty-title">No knowledge found</p>
        <p class="empty-help">
          Try adjusting your search or filter to find what you are looking for.
        </p>
      </div>
    </div>
  {/if}
</div>

<ConfirmDialog
  open={deleting !== undefined}
  title="Are you sure?"
  onconfirm={() => {
    if (deleting) ondelete?.(deleting);
    deleting = undefined;
  }}
  oncancel={() => (deleting = undefined)}
/>

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

  /* Knowledge caps the filters at 55 % of the row, 2 px apart (look §4.1). */
  .filters {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 2px;
    max-inline-size: 55%;
    overflow-x: auto;
    scrollbar-width: none;
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
