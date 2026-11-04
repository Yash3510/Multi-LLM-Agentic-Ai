<script lang="ts">
  // The workspace (workspace look §1-2): the tab row with the Create control, then the current
  // tab's screen. Models is built; the other tabs follow one at a time.
  import { m } from '$lib/i18n/generated/messages.js';
  import Menu from '$lib/ui/components/Menu.svelte';
  import ModelRow from '$lib/ui/components/ModelRow.svelte';
  import WorkspaceTabs from '$lib/ui/components/WorkspaceTabs.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  const VIEWS = { all: 'All', mine: 'Created by you', shared: 'Shared with you' } as const;
  const models = $derived(
    data.models.filter((model) => model.name.toLowerCase().includes(query.trim().toLowerCase())),
  );
</script>

<svelte:head><title>Workspace / {m.app_name()}</title></svelte:head>

<div class="workspace">
  <header class="bar">
    <WorkspaceTabs current={data.tab} counts={data.counts} />
    <span class="create">
      <button type="button" class="create-main">Create</button>
      <button type="button" class="create-more" aria-label="Open create menu">
        <Icon name="caret-down" size={10} />
      </button>
    </span>
  </header>

  {#if data.tab === 'models'}
    <div class="screen">
      <div class="toolbar">
        <label class="search">
          <span class="search-icon"><Icon name="magnifying-glass" size={14} /></span>
          <input
            bind:value={query}
            placeholder="Search Models"
            maxlength="500"
            aria-label="Search Models"
          />
          {#if query}
            <button
              type="button"
              class="clear"
              aria-label="Clear search"
              onclick={() => (query = '')}
            >
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
                options: [
                  { value: 'all', label: VIEWS.all },
                  { value: 'mine', label: VIEWS.mine },
                  { value: 'shared', label: VIEWS.shared },
                ],
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
            label="Actions"
            backLabel="Back"
            align="end"
            items={[
              { id: 'enable', label: 'Enable All', icon: 'mark-unread' },
              { id: 'disable', label: 'Disable All', icon: 'minus' },
              { type: 'separator' },
              { id: 'show', label: 'Show All', icon: 'eye' },
              { id: 'hide', label: 'Hide All', icon: 'eye-slash' },
            ]}
          >
            {#snippet trigger({ props })}
              <button {...props} class="filter actions" title="Actions"
                >Actions<Icon name="caret-down" size={12} /></button
              >
            {/snippet}
          </Menu>
        </div>
      </div>

      {#if models.length}
        <div class="rows">
          {#each models as model (model.id)}<ModelRow {model} />{/each}
        </div>
      {:else}
        <div class="empty">
          <div class="empty-inner">
            <p class="empty-title">No models found</p>
            <p class="empty-help">
              Try adjusting your search or filter to find what you are looking for.
            </p>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .workspace {
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
    block-size: 100%;
  }

  /* The bar (workspace look §1.2): 8 px top, 10 px sides, 4 px bottom; blurred, no fill. */
  .bar {
    display: flex;
    align-items: center;
    padding: var(--spacing-2) 10px 4px;
    backdrop-filter: blur(24px);
    user-select: none;
  }

  /* Create (look §1.3): one joined box; the chevron opens the create menu. */
  .create {
    display: flex;
    flex-shrink: 0;
    margin-inline-start: auto;
    overflow: hidden;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    color: var(--color-gray-900);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .create-main,
  .create-more {
    padding: 4px 10px;
    transition: background-color 150ms;
  }

  .create-more {
    display: grid;
    place-items: center;
    padding-inline: 6px;
    border-inline-start: 1px solid var(--color-gray-200);
  }

  :is(.create-main, .create-more):hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .create {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
    color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .create-more {
    border-color: var(--color-gray-800);
  }

  :global([data-theme='dark']) :is(.create-main, .create-more):hover {
    background-color: var(--color-gray-800);
  }

  .screen {
    display: flex;
    flex-direction: column;
    gap: 4px;
    /* 12 px each side, measured against the running app. */
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

  .filters {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 4px;
    max-inline-size: 60%;
    overflow-x: auto;
    scrollbar-width: none;
  }

  /* The running app's label box is 5 px wider than its text, which sets the caret apart. */
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
    transition: color 150ms;
  }

  .filter.actions {
    gap: 6px;
    max-inline-size: 112px;
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

  .rows {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-block-start: 4px;
  }

  /* Empty (look §2.4): 64 px above, 96 below, a 384 px centred block. */
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

  :is(.create-main, .create-more, .filter, .clear):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
