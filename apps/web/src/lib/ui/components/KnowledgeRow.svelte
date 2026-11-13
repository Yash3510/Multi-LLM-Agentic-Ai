<script lang="ts">
  // One knowledge base in the list (workspace look §4.2): name, badges and age on the first line,
  // the summary under it, the owner, and the more menu for those who may change it. The whole row
  // opens the base.
  import type { KnowledgeBase } from '$lib/data';
  import { ago, longDate } from '$lib/ui/ago';
  import { badges, summary } from '$lib/ui/knowledge';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Menu from './Menu.svelte';

  type Props = {
    base: KnowledgeBase;
    admin?: boolean;
    onopen?: (id: string) => void;
    ondelete?: (id: string) => void;
  };

  let { base, admin = false, onopen, ondelete }: Props = $props();

  const line = $derived(summary(base));

  // Presses on the menu inside do not open the base (F61).
  function open(event: Event) {
    if (event.target instanceof Element && event.target.closest('button, a, input, [role="menu"]'))
      return;
    onopen?.(base.id);
  }

  function key(event: KeyboardEvent) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open(event);
  }
</script>

<div class="row" role="button" tabindex="0" onclick={open} onkeydown={key}>
  <div class="text">
    <div class="line">
      <span class="name" title={base.description || base.name}>{base.name}</span>
      {#each badges(base) as badge (badge)}<span class="badge">{badge}</span>{/each}
      <span class="age" title={longDate.format(base.updated)}>{ago(base.updated)}</span>
    </div>
    {#if line}<div class="summary" title={line}>{line}</div>{/if}
  </div>
  {#if base.owner}
    <span class="owner" title={base.owner.email}>
      {base.owner.name.charAt(0).toUpperCase() + base.owner.name.slice(1)}
    </span>
  {/if}
  {#if base.writable || admin}
    <span class="controls">
      <Menu
        label="More Options"
        backLabel="Back"
        align="end"
        icon="dots-three"
        items={[
          ...(admin ? [{ id: 'export', label: 'Export', icon: 'download-simple' as const }] : []),
          {
            id: 'delete',
            label: 'Delete',
            icon: 'trash' as const,
            onSelect: () => ondelete?.(base.id),
          },
        ]}
      >
        {#snippet trigger({ props })}
          <button {...props} class="more" title="More"><Icon name="dots-three" size={16} /></button>
        {/snippet}
      </Menu>
    </span>
  {/if}
</div>

<style>
  .row {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    inline-size: 100%;
    min-block-size: 32px;
    padding: 4px var(--spacing-2);
    overflow: hidden;
    border-radius: 12px;
    cursor: pointer;
  }

  .row:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }

  .text {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
    overflow: hidden;
  }

  .line {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    min-inline-size: 0;
  }

  .name {
    overflow: hidden;
    color: var(--color-gray-800);
    font-size: var(--text-small);
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .row:hover .name {
    text-decoration: underline;
  }

  .badge {
    padding: 0 5px;
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-500) 20%, transparent);
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    line-height: 16px;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .age {
    flex-shrink: 0;
    overflow: hidden;
    color: var(--color-gray-400);
    font-size: var(--text-micro);
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .summary {
    margin-block-start: 2px;
    overflow: hidden;
    color: var(--color-gray-400);
    font-size: var(--text-micro);
    line-height: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .owner {
    display: none;
    flex-shrink: 0;
    max-inline-size: 176px;
    overflow: hidden;
    color: var(--color-gray-500);
    font-size: var(--text-micro);
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

  .controls {
    display: flex;
    flex-shrink: 0;
    margin-inline-start: var(--spacing-2);
  }

  .more {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    border-radius: 8px;
    color: var(--color-gray-400);
    transition: color 150ms;
  }

  .more:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) :is(.age, .summary) {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .badge {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .more {
    color: var(--color-gray-500);
  }
</style>
