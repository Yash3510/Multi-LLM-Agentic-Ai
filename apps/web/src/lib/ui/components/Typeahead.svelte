<script lang="ts">
  // The workspace type-ahead (workspace F54, look §3.5): a text trigger that opens a search card.
  // The first row adds every match at once; a row toggles one item and closes the card. Closing
  // clears the search.
  import { Popover } from 'bits-ui';
  import type { WorkspaceItem } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { matching } from '$lib/ui/model-editor';

  type Props = {
    label: string;
    search: string;
    empty: string;
    items: WorkspaceItem[];
    selected: string[];
    onchange: (selected: string[]) => void;
  };

  let { label, search, empty, items, selected, onchange }: Props = $props();

  let open = $state(false);
  let query = $state('');
  const found = $derived(matching(items, query));

  function close() {
    open = false;
    query = '';
  }

  function toggle(id: string) {
    onchange(selected.includes(id) ? selected.filter((one) => one !== id) : [...selected, id]);
    close();
  }

  function enableAll() {
    onchange([...new Set([...selected, ...found.map((item) => item.id)])]);
    close();
  }
</script>

<Popover.Root bind:open onOpenChange={(next) => !next && (query = '')}>
  <Popover.Trigger class="typeahead-trigger">{label}</Popover.Trigger>
  <Popover.Portal>
    <Popover.Content class="typeahead" side="bottom" align="start" sideOffset={4}>
      <label class="search">
        <Icon name="magnifying-glass" size={14} />
        <input bind:value={query} placeholder={search} aria-label={search} />
      </label>
      <div class="list">
        {#if found.length}
          <button type="button" class="row" onclick={enableAll}>Enable all ({found.length})</button>
          {#each found as item (item.id)}
            <button type="button" class="row" onclick={() => toggle(item.id)}>
              <span class="truncate">{item.name || item.id}</span>
              {#if selected.includes(item.id)}<Icon name="check-bold" size={14} />{/if}
            </button>
          {/each}
        {:else}
          <p class="empty">{empty}</p>
        {/if}
      </div>
    </Popover.Content>
  </Popover.Portal>
</Popover.Root>

<style>
  :global(.typeahead-trigger) {
    overflow: hidden;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :global(.typeahead-trigger:hover) {
    text-decoration: underline;
  }

  :global([data-theme='dark'] .typeahead-trigger) {
    color: var(--color-gray-400);
  }

  :global(.typeahead) {
    z-index: 10000;
    display: flex;
    flex-direction: column;
    inline-size: min(384px, calc(100vw - 32px));
    padding: 2px;
    border: 1px solid var(--color-gray-200);
    border-radius: 12px;
    background-color: var(--color-white);
    box-shadow:
      0 10px 15px -3px rgb(0 0 0 / 0.1),
      0 4px 6px -4px rgb(0 0 0 / 0.1);
    color: var(--color-black);
  }

  :global([data-theme='dark'] .typeahead) {
    border-color: var(--color-gray-800);
    background-color: var(--color-gray-850);
    color: var(--color-white);
  }

  .search {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0 6px 2px;
  }

  .search input {
    inline-size: 100%;
    padding-block: 2px;
    background: transparent;
    font-size: var(--text-small);
  }

  .search input:focus {
    outline: none;
  }

  .search input::placeholder {
    color: var(--color-gray-400);
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 2px;
    max-block-size: 224px;
    overflow-y: scroll;
  }

  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    block-size: 27px;
    padding-inline: 8px;
    border-radius: 12px;
    color: var(--color-gray-700);
    font-size: var(--text-small);
    text-align: start;
    transition: color 150ms;
  }

  .row:hover {
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-900);
  }

  .row :global(svg) {
    color: var(--color-gray-500);
  }

  :global([data-theme='dark']) .row {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .row:hover {
    background-color: color-mix(in srgb, var(--color-gray-800) 40%, transparent);
    color: var(--color-gray-100);
  }

  .empty {
    padding: 16px 0 24px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    text-align: center;
  }
</style>
