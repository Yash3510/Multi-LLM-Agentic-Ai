<script lang="ts">
  // One folder or document in a knowledge base (workspace look §5.4, F75, F76): icon, name (and
  // size), age, owner, and the more menu for those who may change it. Double-click renames in place.
  import type { KnowledgeDocument, KnowledgeFolder } from '$lib/data';
  import { ago, longDate } from '$lib/ui/ago';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { fileSize } from '$lib/ui/knowledge';
  import Menu from './Menu.svelte';

  type Props = {
    item: KnowledgeFolder | KnowledgeDocument;
    kind: 'folder' | 'document';
    writable: boolean;
    onopen: () => void;
    onrename: (name: string) => void;
    ondelete: () => void;
    ondownload?: () => void;
  };

  let { item, kind, writable, onopen, onrename, ondelete, ondownload }: Props = $props();

  let renaming = $state(false);
  const doc = $derived(kind === 'document' ? (item as KnowledgeDocument) : undefined);

  function finish(input: HTMLInputElement) {
    const name = input.value.trim();
    renaming = false;
    if (name && name !== item.name) onrename(name);
  }

  // Opens with the name selected; Enter or leaving saves, Escape cancels (F75).
  const field = (input: HTMLInputElement) => {
    input.select();
  };
</script>

<div class="row">
  <button type="button" class="icon" aria-label={item.name} onclick={onopen}>
    <Icon name={kind === 'folder' ? 'folder' : 'file-text'} size={14} />
  </button>
  {#if renaming}
    <input
      class="rename"
      value={item.name}
      aria-label="Name"
      {@attach field}
      onblur={(event) => finish(event.currentTarget)}
      onkeydown={(event) => {
        if (event.key === 'Enter') event.currentTarget.blur();
        if (event.key === 'Escape') renaming = false;
        if (event.key === ' ') event.stopPropagation();
      }}
    />
  {:else}
    <button
      type="button"
      class="main"
      onclick={onopen}
      ondblclick={() => writable && (renaming = true)}
    >
      <span class="name">
        {item.name}
        {#if doc?.size !== undefined}<span class="size">{fileSize(doc.size)}</span>{/if}
      </span>
      <span class="facts">
        <span class="age" title={longDate.format(item.updated)}>{ago(item.updated)}</span>
        {#if doc}
          <span class="owner" title={doc.owner?.email ?? 'Deleted User'}
            >By {doc.owner?.name ?? 'Deleted User'}</span
          >
        {/if}
      </span>
    </button>
  {/if}
  {#if writable}
    <Menu
      label="More"
      backLabel="Back"
      align="end"
      items={[
        { id: 'rename', label: 'Rename', icon: 'rename', onSelect: () => (renaming = true) },
        ...(doc
          ? [
              {
                id: 'download',
                label: 'Download',
                icon: 'download-simple' as const,
                onSelect: () => ondownload?.(),
              },
            ]
          : []),
        { id: 'delete', label: 'Delete', icon: 'trash', onSelect: ondelete },
      ]}
    >
      {#snippet trigger({ props })}
        <button {...props} class="more"><Icon name="dots-three" size={14} /></button>
      {/snippet}
    </Menu>
  {/if}
</div>

<style>
  .row {
    display: flex;
    align-items: center;
    inline-size: 100%;
    padding-inline: 8px;
    border-radius: 12px;
    transition: background-color 150ms;
  }

  /* In light the hover is white on the white card, so it shows only in dark (look §5.4). */
  :global([data-theme='dark']) .row:hover {
    background-color: color-mix(in srgb, var(--color-gray-850) 50%, transparent);
  }

  .icon,
  .more {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    padding: 4px;
    border-radius: var(--radius-pill);
    transition: background-color 150ms;
  }

  .more:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .more:hover {
    background-color: var(--color-gray-850);
  }

  .main {
    display: flex;
    flex: 1;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
    min-inline-size: 0;
    padding: 8px;
    border-radius: 12px;
    font-size: var(--text-caption);
    line-height: 16px;
    text-align: start;
  }

  .name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .size {
    color: var(--color-gray-500);
    font-size: var(--text-micro);
  }

  .facts {
    display: flex;
    flex-shrink: 0;
    gap: 8px;
  }

  .age {
    color: var(--color-gray-400);
  }

  .owner {
    color: var(--color-gray-500);
  }

  .rename {
    flex: 1;
    padding: 8px;
    background: transparent;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .rename:focus {
    outline: none;
  }

  :is(.icon, .main, .more):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
