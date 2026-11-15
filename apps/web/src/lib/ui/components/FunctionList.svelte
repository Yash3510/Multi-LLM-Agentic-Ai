<script lang="ts">
  // The Functions list (admin look §15, F133 to F155), shown read only: search, view and type
  // filters, sort by title or date, Export JSON. Saving, enabling, cloning, importing and deleting
  // wait for the 4CE server, so they say so and change nothing. Import From Link, Share and the
  // support link reach outside the machine and are left out, as the owner chose.
  import { DropdownMenu } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { DataSource, ServerFunction } from '$lib/data';
  import { ago, longDate } from '$lib/ui/ago';
  import { NOT_YET } from '$lib/ui/functions';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Switch from './Switch.svelte';
  import './menu.css';
  import './surfaces.css';

  type Props = { source: DataSource; selfEmail?: string };

  let { source, selfEmail }: Props = $props();

  type Type = ServerFunction['type'];
  let functions = $state<ServerFunction[]>();
  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  let type = $state<Type>();
  let sort = $state<{ column: 'name' | 'updated'; ascending: boolean }>({
    column: 'updated',
    ascending: false,
  });
  let notice = $state('');
  let picker = $state<HTMLInputElement>();

  async function load() {
    functions = await source.listFunctions();
  }
  void load();

  const shown = $derived.by(() => {
    const value = query.trim().toLowerCase();
    const sign = sort.ascending ? 1 : -1;
    return (functions ?? [])
      .filter((one) => `${one.name} ${one.id}`.toLowerCase().includes(value))
      .filter((one) => !type || one.type === type)
      .filter((one) => view === 'all' || (view === 'mine') === (one.owner.email === selfEmail))
      .sort((a, b) =>
        sort.column === 'name'
          ? sign * a.name.localeCompare(b.name)
          : sign * (a.updated.getTime() - b.updated.getTime()),
      );
  });

  const VIEWS: ['all' | 'mine' | 'shared', string][] = [
    ['all', 'All'],
    ['mine', 'Created by you'],
    ['shared', 'Shared with you'],
  ];
  const TYPES: Type[] = ['pipe', 'filter', 'action', 'event'];

  const notYet = () => (notice = NOT_YET);
  const sortBy = (column: 'name' | 'updated') =>
    (sort =
      sort.column === column
        ? { column, ascending: !sort.ascending }
        : { column, ascending: column === 'name' });

  function exportJson(list: ServerFunction[]) {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([JSON.stringify(list)], { type: 'application/json' }));
    link.download = `functions-export-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
</script>

<div class="functions">
  <div class="heading">
    <span class="title">Functions <span class="count">{shown.length}</span></span>
    <span class="create">
      <a class="create-main" href={resolve('/admin/functions/create')}>Create</a>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger class="create-more" aria-label="Open create menu">
          <Icon name="caret-down-bold" size={10} />
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            class="fn-menu"
            data-menu
            data-surface="float"
            align="end"
            sideOffset={6}
          >
            <DropdownMenu.Item data-menu-row>
              {#snippet child({ props })}
                <a {...props} href={resolve('/admin/functions/create')}
                  ><span data-menu-lead><Icon name="rename" size={14} /></span>Create</a
                >
              {/snippet}
            </DropdownMenu.Item>
            <DropdownMenu.Item data-menu-row onSelect={() => picker?.click()}>
              <span data-menu-lead><Icon name="file-arrow-up" size={14} /></span>Import JSON
            </DropdownMenu.Item>
            {#if functions?.length}
              <DropdownMenu.Item data-menu-row onSelect={() => exportJson(functions ?? [])}>
                <span data-menu-lead><Icon name="file-arrow-down" size={14} /></span>Export JSON
              </DropdownMenu.Item>
            {/if}
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </span>
  </div>
  <input
    bind:this={picker}
    type="file"
    accept=".json"
    hidden
    aria-label="Functions file"
    onchange={notYet}
  />

  <div class="toolbar">
    <label class="search">
      <Icon name="magnifying-glass" size={14} />
      <input bind:value={query} placeholder="Search Functions" aria-label="Search Functions" />
      {#if query}
        <button type="button" class="clear" aria-label="Clear search" onclick={() => (query = '')}
          ><Icon name="x-bold" size={12} /></button
        >
      {/if}
    </label>
    <div class="filters">
      <DropdownMenu.Root>
        <DropdownMenu.Trigger class="fn-filter">
          {VIEWS.find(([value]) => value === view)?.[1]}<Icon name="caret-down-bold" size={14} />
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            class="fn-menu"
            data-menu
            data-surface="float"
            align="end"
            sideOffset={4}
          >
            {#each VIEWS as [value, label] (value)}
              <DropdownMenu.Item data-menu-row onSelect={() => (view = value)}>
                <span class="grow">{label}</span>
                <span class:hidden={view !== value}><Icon name="check" size={16} /></span>
              </DropdownMenu.Item>
            {/each}
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger class="fn-filter cap">
          {type ?? 'Tag'}
          {#if !type}<Icon name="caret-down-bold" size={14} />{/if}
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            class="fn-menu"
            data-menu
            data-surface="float"
            align="end"
            sideOffset={4}
          >
            {#each TYPES as value (value)}
              <DropdownMenu.Item data-menu-row onSelect={() => (type = value)}>
                <span class="grow cap">{value}</span>
                <span class:hidden={type !== value}><Icon name="check" size={16} /></span>
              </DropdownMenu.Item>
            {/each}
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
      {#if type}
        <button
          type="button"
          class="reset"
          aria-label="Clear type"
          onclick={() => (type = undefined)}><Icon name="x" size={14} /></button
        >
      {/if}
    </div>
  </div>

  {#if notice}<p class="notice" role="status">{notice}</p>{/if}

  {#if functions && !shown.length}
    <div class="empty">
      <p class="empty-title">No functions found</p>
      <p class="empty-hint">
        Try adjusting your search or filter to find what you are looking for.
      </p>
    </div>
  {:else if functions}
    <div class="columns">
      <button type="button" class="col-title" onclick={() => sortBy('name')}>
        Title
        {#if sort.column === 'name'}<Icon
            name={sort.ascending ? 'caret-up' : 'caret-down'}
            size={8}
          />{/if}
      </button>
      <span class="spacer"></span>
      <button type="button" class="col-date" onclick={() => sortBy('updated')}>
        Updated at
        {#if sort.column === 'updated'}<Icon
            name={sort.ascending ? 'caret-up' : 'caret-down'}
            size={8}
          />{/if}
      </button>
    </div>
    <ul class="rows">
      {#each shown as fn (fn.id)}
        <li class="row">
          <a class="main" href="{resolve('/admin/functions/edit')}?id={fn.id}">
            <span class="top">
              <span class="type">{fn.type}</span>
              <span class="name" title={fn.id}>{fn.name}</span>
              {#if fn.version}<span class="version">v{fn.version}</span>{/if}
              <span class="age" title={longDate.format(fn.updated)}>{ago(fn.updated)}</span>
            </span>
            {#if fn.description}<span class="description" title={fn.description}
                >{fn.description}</span
              >{/if}
          </a>
          <span class="owner" title={fn.owner.email}>{fn.owner.name}</span>
          <span class="actions">
            <button
              type="button"
              class="icon"
              aria-label="Settings"
              title="Settings"
              onclick={notYet}><Icon name="gear-six" size={16} /></button
            >
            <DropdownMenu.Root>
              <DropdownMenu.Trigger class="icon" aria-label="Function Menu" title="More">
                <Icon name="dots-three" size={16} />
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content
                  class="fn-menu wide"
                  data-menu
                  data-surface="float"
                  align="end"
                  sideOffset={4}
                >
                  {#if fn.type === 'filter' || fn.type === 'action'}
                    <div class="global">
                      <span><Icon name="globe-simple" size={16} /> Global</span>
                      <Switch on={fn.global === true} label="Global" onchange={notYet} />
                    </div>
                    <DropdownMenu.Separator data-menu-separator />
                  {/if}
                  <DropdownMenu.Item data-menu-row>
                    {#snippet child({ props })}
                      <a {...props} href="{resolve('/admin/functions/edit')}?id={fn.id}"
                        ><span data-menu-lead><Icon name="rename" size={14} /></span>Edit</a
                      >
                    {/snippet}
                  </DropdownMenu.Item>
                  <DropdownMenu.Item data-menu-row onSelect={notYet}>
                    <span data-menu-lead><Icon name="copy" size={14} /></span>Clone
                  </DropdownMenu.Item>
                  <DropdownMenu.Item data-menu-row onSelect={() => exportJson([fn])}>
                    <span data-menu-lead><Icon name="download-simple" size={14} /></span>Export
                  </DropdownMenu.Item>
                  <DropdownMenu.Separator data-menu-separator />
                  <DropdownMenu.Item data-menu-row onSelect={notYet}>
                    <span data-menu-lead><Icon name="trash-bold" size={14} /></span>Delete
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
            <span class="toggle"><Switch on={fn.enabled} onchange={notYet} /></span>
          </span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .functions {
    inline-size: 100%;
    padding-inline: 10px;
    font-size: var(--text-ui);
  }

  .heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 2px 0 4px;
    padding-inline: 4px;
  }

  .title {
    display: flex;
    flex-shrink: 0;
    gap: 6px;
    padding-inline: 2px;
  }

  .count {
    color: color-mix(in srgb, var(--color-gray-500) 60%, transparent);
  }

  .create {
    display: flex;
    margin-inline-start: 4px;
    overflow: hidden;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    color: var(--color-gray-900);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .create {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
    color: var(--color-gray-100);
  }

  .create-main {
    padding: 4px 10px;
    line-height: 16px;
  }

  .create-main:hover,
  :global(.create-more:hover) {
    background-color: var(--color-gray-100);
  }

  :global(.create-more) {
    display: grid;
    place-items: center;
    padding: 4px 6px;
    border-inline-start: 1px solid var(--color-gray-200);
  }

  :global([data-theme='dark'] .create-more) {
    border-color: var(--color-gray-800);
  }

  :global(.fn-menu) {
    z-index: 9999;
    min-inline-size: 170px;
  }

  :global(.fn-menu.wide) {
    min-inline-size: 180px;
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    block-size: 32px;
  }

  .search {
    display: flex;
    flex: 1;
    align-items: center;
    min-inline-size: 0;
    border-radius: var(--radius-pill);
    padding-inline: 12px;
    background-image: var(--field-inset-fill);
    box-shadow: var(--field-inset-edge);
  }

  .search > :global(svg) {
    flex-shrink: 0;
    margin-inline: 4px 12px;
  }

  .search input {
    inline-size: 100%;
    padding-block: 4px;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
  }

  .search input:focus {
    outline: none;
  }

  .search input::placeholder {
    color: var(--color-gray-400);
  }

  .clear {
    display: grid;
    padding: 2px;
    border-radius: var(--radius-pill);
  }

  .filters {
    display: flex;
    flex-shrink: 0;
    gap: 2px;
    max-inline-size: 55%;
    overflow-x: auto;
    scrollbar-width: none;
  }

  :global(.fn-filter) {
    display: flex;
    align-items: center;
    gap: 2px;
    block-size: 32px;
    padding: 6px;
    border-radius: 12px;
    color: var(--color-gray-700);
    font-size: 13px;
    transition: color 150ms;
  }

  :global(.fn-filter:hover) {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark'] .fn-filter) {
    color: var(--color-gray-200);
  }

  .cap,
  :global(.fn-filter.cap) {
    text-transform: capitalize;
  }

  .reset {
    display: grid;
    place-items: center;
  }

  .grow {
    flex: 1;
  }

  .hidden {
    visibility: hidden;
  }

  .notice {
    margin: 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .columns {
    display: flex;
    gap: 8px;
    padding: 0 6px 2px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .columns {
    color: var(--color-gray-600);
  }

  .col-title {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 4px;
    padding-block: 2px;
  }

  .spacer {
    display: none;
    inline-size: 176px;
  }

  @media (min-width: 48rem) {
    .spacer {
      display: block;
    }
  }

  .col-date {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 4px;
    inline-size: 144px;
  }

  .rows {
    display: grid;
    gap: 2px;
  }

  .row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-block-size: 32px;
    padding: 4px 8px;
    overflow: hidden;
    border-radius: 12px;
  }

  .main {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
  }

  .top {
    display: flex;
    align-items: center;
    gap: 8px;
    min-inline-size: 0;
  }

  .type {
    padding-inline: 4px;
    border-radius: 4px;
    background-color: color-mix(in srgb, var(--color-gray-500) 20%, transparent);
    color: var(--color-gray-700);
    font-size: 10px;
    line-height: 16px;
    text-transform: uppercase;
  }

  :global([data-theme='dark']) .type {
    color: var(--color-gray-200);
  }

  .name {
    overflow: hidden;
    color: var(--color-gray-800);
    font-size: 13px;
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .row:hover .name {
    text-decoration: underline;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-gray-200);
  }

  .version {
    max-inline-size: 40%;
    overflow: hidden;
    color: var(--color-gray-500);
    font-size: 11px;
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .age,
  .description {
    color: var(--color-gray-400);
    font-size: 11px;
  }

  .age {
    line-height: 20px;
  }

  :global([data-theme='dark']) :is(.age, .description) {
    color: var(--color-gray-600);
  }

  .description {
    margin-block-start: 2px;
    overflow: hidden;
    line-height: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .owner {
    display: none;
    max-inline-size: 176px;
    overflow: hidden;
    color: var(--color-gray-500);
    font-size: 11px;
    line-height: 20px;
    text-align: end;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  @media (min-width: 48rem) {
    .owner {
      display: block;
    }
  }

  .actions {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    margin-inline-start: 8px;
  }

  .actions :global(.icon) {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    border-radius: 8px;
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .actions :global(.icon) {
    color: var(--color-gray-500);
  }

  .toggle {
    display: flex;
    align-items: center;
    block-size: 24px;
  }

  .global {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-block-size: 27px;
    padding-inline: 8px;
    font-size: 13px;
  }

  .global span {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .empty {
    max-inline-size: 384px;
    margin-inline: auto;
    padding: 64px 0 96px;
    text-align: center;
  }

  .empty-title {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .empty-title {
    color: var(--color-gray-100);
  }

  .empty-hint {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 20px;
  }

  :is(.create-main, .clear, .reset, .col-title, .col-date, .main):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
