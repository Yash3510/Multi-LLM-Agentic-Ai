<script lang="ts">
  // The admin Groups tab (admin look §11, F54 to F63): search, the sort menu (Members or Name),
  // New Group, the group rows and the Default permissions row.
  import { DropdownMenu } from 'bits-ui';
  import type { DataSource, Group } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { hasCustom } from '$lib/ui/permissions';
  import './menu.css';
  import './surfaces.css';

  type Props = {
    source: DataSource;
    version?: number;
    onnew?: () => void;
    onedit?: (group: Group) => void;
    ondefaults?: () => void;
    /** Tells the page how many groups are shown. */
    oncount?: (count: number) => void;
  };

  let { source, version = 0, onnew, onedit, ondefaults, oncount }: Props = $props();

  let groups = $state<Group[]>();
  let query = $state('');
  let sort = $state<'members' | 'name'>('members');

  $effect(() => {
    void version;
    void source.listGroups().then((loaded) => (groups = loaded));
  });

  const shown = $derived.by(() => {
    const value = query.trim().toLowerCase();
    return (groups ?? [])
      .filter((one) => one.name.toLowerCase().includes(value))
      .sort((a, b) =>
        sort === 'members' && b.members.length !== a.members.length
          ? b.members.length - a.members.length
          : a.name.localeCompare(b.name),
      );
  });

  $effect(() => {
    if (groups) oncount?.(shown.length);
  });

  const SORTS: ['members' | 'name', string][] = [
    ['members', 'Members'],
    ['name', 'Name'],
  ];
</script>

{#if groups}
  <div class="toolbar">
    <label class="search">
      <Icon name="magnifying-glass" size={14} />
      <input bind:value={query} placeholder="Search Groups" aria-label="Search Groups" />
      {#if query}
        <button type="button" class="clear" aria-label="Clear search" onclick={() => (query = '')}
          ><Icon name="x-bold" size={12} /></button
        >
      {/if}
    </label>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger class="group-sort">
        {sort === 'members' ? 'Members' : 'Name'}<Icon name="caret-down-bold" size={14} />
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          class="group-sort-menu"
          data-menu
          data-surface="float"
          align="end"
          sideOffset={4}
        >
          {#each SORTS as [value, label] (value)}
            <DropdownMenu.Item data-menu-row onSelect={() => (sort = value)}>
              <span class="sort-label">{label}</span>
              <span class="check" class:hidden={sort !== value}
                ><Icon name="check" size={16} /></span
              >
            </DropdownMenu.Item>
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
    <button type="button" class="new" onclick={onnew}>New Group</button>
  </div>

  {#if shown.length}
    <ul class="list">
      {#each shown as group (group.id)}
        <li>
          <button type="button" class="row" onclick={() => onedit?.(group)}>
            <span class="text">
              <span class="line">
                <span class="name">{group.name}</span>
                <span class="chip">{group.members.length} members</span>
              </span>
              <span class="sub">
                <span class="clamp">{group.description || 'No description'}</span>
                <span class="slash" aria-hidden="true">/</span>
                <span>{hasCustom(group.permissions) ? 'Custom permissions' : 'Uses defaults'}</span>
              </span>
            </span>
            <span class="edit">Edit</span>
          </button>
        </li>
      {/each}
    </ul>
  {:else}
    <div class="empty">
      <p class="empty-title">No groups found</p>
      <p class="empty-hint">Use groups to organize your users and assign permissions.</p>
    </div>
  {/if}

  <div class="divider"></div>
  <button type="button" class="row" onclick={ondefaults}>
    <span class="text">
      <span class="name">Default permissions</span>
      <span class="sub"><span class="clamp">applies to all users with the "user" role</span></span>
    </span>
    <span class="edit">Edit</span>
  </button>
{/if}

<style>
  .toolbar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 8px;
    block-size: 32px;
    background-color: var(--color-white);
    font-size: var(--text-ui);
  }

  :global([data-theme='dark']) .toolbar {
    background-color: var(--color-gray-900);
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
    padding-inline-end: 16px;
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
    margin-inline-start: 6px;
    padding: 2px;
    border-radius: var(--radius-pill);
  }

  .clear:hover {
    background-color: var(--color-gray-100);
  }

  :global(.group-sort) {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 4px;
    block-size: 32px;
    padding: 6px;
    border-radius: 12px;
    color: var(--color-gray-700);
    font-size: 13px;
    transition: color 150ms;
  }

  :global(.group-sort:hover) {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark'] .group-sort) {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark'] .group-sort:hover) {
    color: var(--color-gray-100);
  }

  :global(.group-sort-menu) {
    z-index: 9999;
    min-inline-size: 170px;
  }

  .sort-label {
    flex: 1;
  }

  .check.hidden {
    visibility: hidden;
  }

  .new {
    flex-shrink: 0;
    margin-inline-start: 4px;
    padding: 4px 10px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    color: var(--color-gray-900);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: background-color 150ms;
  }

  .new:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .new {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
    color: var(--color-gray-100);
  }

  .list {
    margin-block-start: 4px;
  }

  .list li + li {
    border-block-start: 1px solid var(--color-gray-50);
  }

  :global([data-theme='dark']) .list li + li {
    border-color: color-mix(in srgb, var(--color-gray-850) 40%, transparent);
  }

  .row {
    display: flex;
    align-items: center;
    gap: 12px;
    inline-size: 100%;
    padding: 8px 10px;
    text-align: start;
  }

  .text {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 2px;
    min-inline-size: 0;
    padding-inline-start: 4px;
  }

  .line {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .name {
    overflow: hidden;
    color: var(--color-gray-900);
    font-size: var(--text-ui);
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .row:hover .name {
    text-decoration: underline;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-gray-100);
  }

  .chip {
    padding: 2px 6px;
    border-radius: 6px;
    background-color: color-mix(in srgb, var(--color-gray-500) 10%, transparent);
    color: var(--color-gray-600);
    font-size: 11px;
    line-height: 1;
  }

  :global([data-theme='dark']) .chip {
    color: var(--color-gray-300);
  }

  .sub {
    display: flex;
    gap: 6px;
    min-inline-size: 0;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .clamp {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .slash {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .slash {
    color: var(--color-gray-700);
  }

  .edit {
    padding-inline: 6px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    transition: color 150ms;
  }

  .row:hover .edit {
    color: var(--color-gray-800);
  }

  :global([data-theme='dark']) .edit {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .row:hover .edit {
    color: var(--color-gray-200);
  }

  .empty {
    max-inline-size: 384px;
    margin-inline: auto;
    padding: 64px 0 96px;
    text-align: center;
  }

  .empty-title {
    margin-block-end: 6px;
    color: var(--color-gray-900);
    font-size: var(--text-ui);
  }

  :global([data-theme='dark']) .empty-title {
    color: var(--color-gray-100);
  }

  .empty-hint {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 20px;
  }

  .divider {
    block-size: 1px;
    margin-block: 4px;
    background-color: var(--color-gray-50);
  }

  :global([data-theme='dark']) .divider {
    background-color: color-mix(in srgb, var(--color-gray-850) 40%, transparent);
  }

  :is(.clear, .new, .row):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
