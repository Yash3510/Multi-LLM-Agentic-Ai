<script lang="ts">
  // One tool in the list (workspace look §9.1, F109, F110): name, version and age, the
  // description under it, the owner, then Settings and the more menu. A tool the person cannot
  // change is dimmed, cannot be opened and has no controls. While Shift is held the controls
  // become one delete button.
  import type { Tool } from '$lib/data';
  import { ago, longDate } from '$lib/ui/ago';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Menu from './Menu.svelte';

  type Props = {
    tool: Tool;
    quick: boolean;
    onopen?: (id: string) => void;
    onsettings?: (tool: Tool) => void;
    onclone?: (tool: Tool) => void;
    onexport?: (tool: Tool) => void;
    ondelete?: (id: string) => void;
    onconfirmdelete?: (tool: Tool) => void;
  };

  let { tool, quick, onopen, onsettings, onclone, onexport, ondelete, onconfirmdelete }: Props =
    $props();

  function open(event: Event) {
    if (event.target instanceof Element && event.target.closest('button, a, input, [role="menu"]'))
      return;
    onopen?.(tool.id);
  }

  function key(event: KeyboardEvent) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open(event);
  }

  const owner = $derived(
    tool.owner ? tool.owner.name.charAt(0).toUpperCase() + tool.owner.name.slice(1) : '',
  );
</script>

{#snippet contents()}
  <div class="text">
    <div class="line">
      <span class="name" title={tool.id}>{tool.name}</span>
      {#if tool.version}<span class="command">v{tool.version}</span>{/if}
      <span class="age" title={longDate.format(tool.updated)}>{ago(tool.updated)}</span>
      {#if !tool.writable}<span class="badge">Read Only</span>{/if}
    </div>
    {#if tool.description}<div class="content" title={tool.description}>
        {tool.description}
      </div>{/if}
  </div>
  {#if owner}<span class="owner" title={tool.owner?.email ?? 'Deleted User'}>{owner}</span>{/if}
  {#if tool.writable}
    <span class="controls">
      {#if quick}
        <button
          type="button"
          class="icon"
          aria-label="Delete"
          title="Delete"
          onclick={() => ondelete?.(tool.id)}><Icon name="trash" size={16} /></button
        >
      {:else}
        <span class="group">
          <button
            type="button"
            class="icon"
            aria-label="Settings"
            title="Settings"
            onclick={() => onsettings?.(tool)}><Icon name="gear-six" size={16} /></button
          >
          <Menu
            label="Tool Menu"
            backLabel="Back"
            align="end"
            items={[
              { id: 'edit', label: 'Edit', icon: 'rename', onSelect: () => onopen?.(tool.id) },
              { id: 'clone', label: 'Clone', icon: 'copy', onSelect: () => onclone?.(tool) },
              {
                id: 'export',
                label: 'Export',
                icon: 'download-simple',
                onSelect: () => onexport?.(tool),
              },
              { type: 'separator' },
              {
                id: 'delete',
                label: 'Delete',
                icon: 'trash',
                onSelect: () => onconfirmdelete?.(tool),
              },
            ]}
          >
            {#snippet trigger({ props })}
              <button {...props} class="icon" aria-label="Tool Menu" title="More"
                ><Icon name="dots-three" size={16} /></button
              >
            {/snippet}
          </Menu>
        </span>
      {/if}
    </span>
  {/if}
{/snippet}

{#if tool.writable}
  <div class="row" role="button" tabindex="0" onclick={open} onkeydown={key}>
    {@render contents()}
  </div>
{:else}
  <!-- A tool the person cannot change is visible but inert (F109). -->
  <div class="row" data-inert>{@render contents()}</div>
{/if}

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

  /* A tool the person cannot change is visible but inert (F109). */
  .row[data-inert] {
    cursor: not-allowed;
    opacity: 0.6;
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

  .command,
  .age {
    flex-shrink: 0;
    overflow: hidden;
    font-size: var(--text-micro);
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .command {
    max-inline-size: 40%;
    color: var(--color-gray-500);
  }

  .age {
    color: var(--color-gray-400);
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

  .content {
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
    align-items: center;
    margin-inline-start: var(--spacing-2);
  }

  .group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .icon {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    border-radius: 8px;
    color: var(--color-gray-400);
    transition: color 150ms;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) :is(.age, .content) {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .icon {
    color: var(--color-gray-500);
  }

  .icon:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
