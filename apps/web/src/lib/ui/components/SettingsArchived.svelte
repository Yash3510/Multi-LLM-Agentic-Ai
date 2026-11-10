<script lang="ts">
  // Archived Chats (chat-composer look §9.13, F102): the count, search, the Actions menu
  // (Unarchive All, Export) and the list, sortable by title or date, with unarchive and delete.
  import { DropdownMenu } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { ChatSummary, DataSource } from '$lib/data';
  import { calendarDay } from '$lib/ui/ago';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import SortHeader from './SortHeader.svelte';
  import { nextSort, type Sort } from './sort';
  import './menu.css';
  import './settings-page.css';
  import './surfaces.css';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  let chats = $state<ChatSummary[]>();
  let query = $state('');
  let sort = $state<Sort>({ column: 'updated', direction: 'descending' });
  let deleting = $state<ChatSummary>();
  let unarchivingAll = $state(false);

  async function load() {
    chats = await source.listArchivedChats();
  }
  void load();

  const shown = $derived.by(() => {
    const value = query.trim().toLowerCase();
    const list = (chats ?? []).filter((chat) => chat.title.toLowerCase().includes(value));
    const sign = sort.direction === 'ascending' ? 1 : -1;
    return list.sort((a, b) =>
      sort.column === 'title'
        ? sign * a.title.localeCompare(b.title)
        : sign * (a.updated.getTime() - b.updated.getTime()),
    );
  });

  async function unarchive(chat: ChatSummary) {
    await source.unarchiveChat(chat.id);
    await load();
  }

  async function remove() {
    if (!deleting) return;
    await source.deleteChat(deleting.id);
    deleting = undefined;
    await load();
  }

  async function unarchiveAll() {
    await source.unarchiveAllChats();
    unarchivingAll = false;
    await load();
  }

  async function exportArchived() {
    const ids = new Set((chats ?? []).map((chat) => chat.id));
    const all = await source.exportChats();
    const blob = new Blob([JSON.stringify(all.filter((chat) => ids.has(chat.id)))], {
      type: 'application/json',
    });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `archived-chat-export-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
</script>

<div class="settings-page archived">
  <h2>
    Archived Chats
    {#if chats}<span class="count">{chats.length}</span>{/if}
  </h2>
  <div class="tools">
    <label class="search">
      <Icon name="magnifying-glass" size={14} />
      <input
        bind:value={query}
        placeholder="Search"
        aria-label="Search archived chats"
        maxlength="500"
      />
      {#if query}
        <button type="button" class="clear" aria-label="Clear search" onclick={() => (query = '')}
          ><Icon name="x-bold" size={12} /></button
        >
      {/if}
    </label>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger class="settings-actions">
        <span>Actions</span><Icon name="caret-down-bold" size={12} />
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          class="settings-menu"
          data-menu
          data-surface="float"
          align="end"
          sideOffset={4}
        >
          <DropdownMenu.Item
            data-menu-row
            disabled={!chats?.length}
            onSelect={() => (unarchivingAll = true)}
          >
            <span data-menu-lead><Icon name="unarchive" size={14} /></span>Unarchive All
          </DropdownMenu.Item>
          <DropdownMenu.Item data-menu-row disabled={!chats?.length} onSelect={exportArchived}>
            <span data-menu-lead><Icon name="download-simple" size={14} /></span>Export
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  </div>
  <div class="body">
    {#if chats && !shown.length}
      <p class="empty">You have no archived conversations.</p>
    {:else if chats}
      <div class="head" role="row">
        <span class="title-col">
          <SortHeader
            column="title"
            label="Title"
            {sort}
            onsort={(column) => (sort = nextSort(sort, column))}
          />
        </span>
        <span class="date-col">
          <SortHeader
            column="updated"
            label="Updated at"
            align="end"
            {sort}
            onsort={(column) => (sort = nextSort(sort, column))}
          />
        </span>
        <span class="actions-col"></span>
      </div>
      <ul>
        {#each shown as chat (chat.id)}
          <li>
            <a class="title" href={resolve('/c/[id]', { id: chat.id })}>{chat.title}</a>
            <span class="date">{calendarDay(chat.updated)}</span>
            <span class="actions">
              <button
                type="button"
                aria-label="Unarchive Chat"
                title="Unarchive Chat"
                onclick={() => unarchive(chat)}><Icon name="unarchive" size={14} /></button
              >
              <button
                type="button"
                aria-label="Delete Chat"
                title="Delete Chat"
                onclick={() => (deleting = chat)}><Icon name="trash" size={14} /></button
              >
            </span>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<ConfirmDialog
  open={deleting !== undefined}
  onconfirm={remove}
  oncancel={() => (deleting = undefined)}
/>

<ConfirmDialog
  open={unarchivingAll}
  message="Are you sure you want to unarchive all archived chats?"
  confirmLabel="Unarchive All"
  onconfirm={unarchiveAll}
  oncancel={() => (unarchivingAll = false)}
/>

<style>
  .archived {
    justify-content: flex-start;
  }

  .archived h2 {
    margin-block-end: 12px;
  }

  .count {
    margin-inline-start: 8px;
    color: var(--color-gray-500);
    font-weight: 400;
  }

  .tools {
    flex-shrink: 0;
    gap: 8px;
    block-size: 28px;
    margin-block-end: 0;
  }

  .body {
    margin-block-start: 12px;
  }

  .empty {
    display: grid;
    place-items: center;
    min-block-size: 80px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  :global([data-theme='dark']) .empty {
    color: var(--color-gray-400);
  }

  .head,
  li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .head {
    gap: 4px;
    padding-inline: 4px;
  }

  .title-col {
    flex: 1;
  }

  .date-col,
  .date {
    display: none;
    flex-shrink: 0;
    inline-size: 96px;
    justify-content: flex-end;
  }

  @media (min-width: 40rem) {
    .date-col,
    .date {
      display: flex;
    }
  }

  .actions-col {
    inline-size: 52px;
  }

  li {
    padding: 4px;
    font-size: var(--text-caption);
  }

  .title {
    flex: 1;
    max-inline-size: 576px;
    overflow: hidden;
    color: var(--color-gray-600);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .title:hover {
    color: var(--color-black);
  }

  :global([data-theme='dark']) .title {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .title:hover {
    color: var(--color-white);
  }

  .date {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .date {
    color: var(--color-gray-600);
  }

  .actions {
    display: flex;
    flex-shrink: 0;
  }

  .actions button {
    display: grid;
    padding: 4px;
    border-radius: 8px;
    color: var(--color-gray-400);
    transition: color 150ms;
  }

  .actions button:hover {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .actions button {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .actions button:hover {
    color: var(--color-gray-300);
  }

  :is(.title, .actions button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
