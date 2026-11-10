<script lang="ts">
  // Personalization (chat-composer look §9.9, F98): the memory switch, saved at once, and the
  // person's memories: search, the Actions menu (Add Memory, Clear memory), Edit and Remove.
  import { DropdownMenu } from 'bits-ui';
  import { untrack } from 'svelte';
  import type { DataSource, Memory, MemoryDraft, UserSettings } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import MemoryDialog from './MemoryDialog.svelte';
  import Switch from './Switch.svelte';
  import './menu.css';
  import './settings-page.css';
  import './surfaces.css';

  type Props = { source: DataSource; settings: UserSettings };

  let { source, settings }: Props = $props();

  let enabled = $state(untrack(() => settings.ui?.memory !== false));
  let memories = $state<Memory[]>();
  let query = $state('');
  let notice = $state('');
  let editing = $state<{ memory?: Memory }>();
  let removing = $state<Memory>();
  let clearing = $state(false);

  const load = async () => (memories = await source.listMemories());
  void load();

  const shown = $derived.by(() => {
    const value = query.trim().toLowerCase();
    if (!value) return memories ?? [];
    return (memories ?? []).filter((one) =>
      [one.content, one.path, one.type].some((part) => part?.toLowerCase().includes(value)),
    );
  });

  async function setEnabled(on: boolean) {
    enabled = on;
    await source.saveUserSettings({ ui: { memory: on } });
  }

  async function save(draft: MemoryDraft) {
    const memory = editing?.memory;
    if (memory) await source.updateMemory(memory.id, draft);
    else await source.addMemory(draft);
    editing = undefined;
    await load();
  }

  async function remove() {
    if (!removing) return;
    await source.deleteMemory(removing.id);
    removing = undefined;
    await load();
  }

  async function clear() {
    await source.clearMemories();
    clearing = false;
    await load();
  }
</script>

<div class="settings-page">
  <h2>Personalization</h2>
  <div class="body">
    <h3>Memory</h3>
    <div class="block">
      <div class="row">
        <span class="label">Memory <span class="experimental">Experimental</span></span>
        <Switch on={enabled} onchange={setEnabled} />
      </div>
      <p class="note">
        You can personalize your interactions with LLMs by adding memories through the 'Add Memory'
        button below, making them more helpful and tailored to you.
      </p>
    </div>
    {#if enabled && memories}
      <div class="saved">
        Saved Memories <span class="count">{memories.length}</span>
      </div>
      <div class="tools">
        {#if memories.length}
          <label class="search">
            <Icon name="magnifying-glass" size={14} />
            <input bind:value={query} placeholder="Search Memories" maxlength="500" />
            {#if query}
              <button
                type="button"
                class="clear"
                aria-label="Clear search"
                onclick={() => (query = '')}><Icon name="x-bold" size={12} /></button
              >
            {/if}
          </label>
        {:else}
          <span class="search"></span>
        {/if}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger class="memory-actions">
            <span>Actions</span><Icon name="caret-down-bold" size={12} />
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              class="memory-menu"
              data-menu
              data-surface="float"
              align="end"
              sideOffset={4}
            >
              <DropdownMenu.Item data-menu-row onSelect={() => (editing = {})}>
                <span data-menu-lead><Icon name="plus" size={14} /></span>Add Memory
              </DropdownMenu.Item>
              <DropdownMenu.Item
                data-menu-row
                disabled={!memories.length}
                onSelect={() => (clearing = true)}
              >
                <span data-menu-lead><Icon name="trash" size={14} /></span>Clear memory
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
      {#if shown.length}
        <ul class="list">
          {#each shown as memory (memory.id)}
            <li>
              <span class="content">{memory.content}</span>
              <span class="actions">
                <button type="button" class="quiet" onclick={() => (editing = { memory })}
                  >Edit</button
                >
                <button type="button" class="quiet" onclick={() => (removing = memory)}
                  >Remove</button
                >
              </span>
            </li>
          {/each}
        </ul>
      {:else}
        <p class="empty">
          {memories.length ? 'No results found' : 'Memories accessible by LLMs will be shown here.'}
        </p>
      {/if}
    {/if}
  </div>
  <p class="sr-only" role="status">{notice}</p>
  <div class="footer">
    <button type="button" class="save" onclick={() => (notice = 'Settings saved successfully!')}
      >Save</button
    >
  </div>
</div>

<MemoryDialog
  open={editing !== undefined}
  memory={editing?.memory}
  onsave={save}
  onclose={() => (editing = undefined)}
/>

<ConfirmDialog
  open={clearing}
  title="Clear Memory"
  message="Are you sure you want to clear all memories? This action cannot be undone."
  onconfirm={clear}
  oncancel={() => (clearing = false)}
/>

<ConfirmDialog
  open={removing !== undefined}
  title="Delete Memory?"
  message="Are you sure you want to delete this memory? This action cannot be undone."
  onconfirm={remove}
  oncancel={() => (removing = undefined)}
>
  <div class="quote">{removing?.content}</div>
</ConfirmDialog>

<style>
  .label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  /* The experimental tag (common look F33). */
  .experimental {
    color: var(--color-gray-400);
    font-size: 10px;
    line-height: 1;
    text-transform: uppercase;
  }

  :global([data-theme='dark']) .experimental {
    color: var(--color-gray-600);
  }

  .block {
    margin-block-end: 10px;
  }

  .saved {
    margin-block-end: 4px;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .count {
    margin-inline-start: 4px;
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .saved {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .count {
    color: var(--color-gray-600);
  }

  .tools {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-block-end: 8px;
  }

  .search {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 8px;
    min-inline-size: 0;
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .search {
    color: var(--color-gray-600);
  }

  .search input {
    flex: 1;
    min-inline-size: 0;
    padding-block: 2px;
    background: transparent;
    color: var(--color-gray-700);
    font-size: var(--text-caption);
  }

  .search input:focus {
    outline: none;
  }

  .search input::placeholder {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .search input {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .search input::placeholder {
    color: var(--color-gray-700);
  }

  .clear {
    display: grid;
    padding: 2px;
    border-radius: 8px;
    transition: color 150ms;
  }

  .clear:hover {
    color: var(--color-gray-700);
  }

  :global(.memory-actions) {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    block-size: 28px;
    padding-inline: 6px;
    border-radius: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: color 150ms;
  }

  :global(.memory-actions:hover) {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark'] .memory-actions:hover) {
    color: var(--color-white);
  }

  :global(.memory-menu) {
    z-index: 9999;
    inline-size: 170px;
    min-inline-size: 170px;
  }

  :global(.memory-menu [data-menu-row]) {
    font-size: var(--text-caption);
  }

  :global(.memory-menu [data-menu-row][data-disabled]) {
    opacity: 0.3;
    cursor: default;
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .list li {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  .content {
    min-inline-size: 0;
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    overflow-wrap: anywhere;
    white-space: pre-wrap;
  }

  :global([data-theme='dark']) .content {
    color: var(--color-gray-300);
  }

  .actions {
    display: flex;
    flex-shrink: 0;
    gap: 8px;
  }

  .actions .quiet:hover {
    text-decoration: underline;
  }

  .empty {
    min-block-size: 64px;
    color: var(--color-gray-400);
    font-size: 11px;
    line-height: 16px;
  }

  :global([data-theme='dark']) .empty {
    color: var(--color-gray-600);
  }

  .quote {
    max-block-size: 128px;
    margin-block-start: 8px;
    padding: 8px;
    overflow-y: auto;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    overflow-wrap: anywhere;
    white-space: pre-wrap;
  }

  :global([data-theme='dark']) .quote {
    border-color: rgb(255 255 255 / 0.04);
    background-color: rgb(255 255 255 / 0.03);
    color: var(--color-gray-400);
  }

  :is(.clear):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
