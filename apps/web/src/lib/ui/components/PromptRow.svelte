<script lang="ts">
  // One prompt in the list (workspace look §6.1, F90, F91): name, command and age, the text under
  // it, the owner, then copy, the more menu and the on/off switch. While Shift is held the
  // controls become one delete button.
  import type { Prompt } from '$lib/data';
  import { ago, longDate } from '$lib/ui/ago';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Menu from './Menu.svelte';

  type Props = {
    prompt: Prompt;
    quick: boolean;
    onopen?: (id: string) => void;
    ontoggle?: (id: string, active: boolean) => void;
    onclone?: (prompt: Prompt) => void;
    onexport?: (prompt: Prompt) => void;
    ondelete?: (id: string) => void;
    onconfirmdelete?: (prompt: Prompt) => void;
  };

  let { prompt, quick, onopen, ontoggle, onclone, onexport, ondelete, onconfirmdelete }: Props =
    $props();

  let copied = $state(false);

  async function copy() {
    await navigator.clipboard?.writeText(prompt.content);
    copied = true;
    setTimeout(() => (copied = false), 2000);
  }

  function open(event: Event) {
    if (event.target instanceof Element && event.target.closest('button, a, input, [role="menu"]'))
      return;
    onopen?.(prompt.id);
  }

  function key(event: KeyboardEvent) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open(event);
  }

  const owner = $derived(
    prompt.owner ? prompt.owner.name.charAt(0).toUpperCase() + prompt.owner.name.slice(1) : '',
  );
</script>

<div class="row" role="button" tabindex="0" onclick={open} onkeydown={key}>
  <div class="text">
    <div class="line">
      <span class="name" title={prompt.name}>{prompt.name}</span>
      <span class="command">/{prompt.command}</span>
      <span class="age" title={longDate.format(prompt.updated)}>{ago(prompt.updated)}</span>
      {#if !prompt.writable}<span class="badge">Read Only</span>{/if}
    </div>
    {#if prompt.content}<div class="content" title={prompt.content}>{prompt.content}</div>{/if}
  </div>
  {#if owner}<span class="owner" title={prompt.owner?.email ?? 'Deleted User'}>{owner}</span>{/if}
  <span class="controls">
    {#if quick}
      <button
        type="button"
        class="icon"
        aria-label="Delete"
        title="Delete"
        onclick={() => ondelete?.(prompt.id)}><Icon name="trash" size={16} /></button
      >
    {:else}
      <button type="button" class="icon" aria-label="Copy Prompt" title="Copy Prompt" onclick={copy}
        ><Icon name={copied ? 'check' : 'clipboard'} size={16} /></button
      >
      <span class="group">
        <Menu
          label="Prompt Menu"
          backLabel="Back"
          align="end"
          items={[
            { id: 'edit', label: 'Edit', icon: 'rename', onSelect: () => onopen?.(prompt.id) },
            { id: 'clone', label: 'Clone', icon: 'copy', onSelect: () => onclone?.(prompt) },
            {
              id: 'export',
              label: 'Export',
              icon: 'download-simple',
              onSelect: () => onexport?.(prompt),
            },
            { type: 'separator' },
            {
              id: 'delete',
              label: 'Delete',
              icon: 'trash',
              onSelect: () => onconfirmdelete?.(prompt),
            },
          ]}
        >
          {#snippet trigger({ props })}
            <button {...props} class="icon" aria-label="Prompt Menu" title="More"
              ><Icon name="dots-three" size={16} /></button
            >
          {/snippet}
        </Menu>
        <button
          type="button"
          class="switch"
          role="switch"
          aria-checked={prompt.active}
          aria-label={prompt.active ? 'Enabled' : 'Disabled'}
          title={prompt.active ? 'Enabled' : 'Disabled'}
          data-on={prompt.active ? '' : undefined}
          onclick={() => ontoggle?.(prompt.id, !prompt.active)}><span class="thumb"></span></button
        >
      </span>
    {/if}
  </span>
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
    margin-inline-start: 2px;
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

  /* The switch (workspace look §0.7): a 28 by 16 track with a 12 px thumb. */
  .switch {
    position: relative;
    inline-size: 28px;
    block-size: 16px;
    margin-inline: 1px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-300);
    transition: background-color 150ms;
  }

  .switch[data-on] {
    background-color: var(--color-gray-900);
  }

  .thumb {
    position: absolute;
    inset-block-start: 2px;
    inset-inline-start: 2px;
    inline-size: 12px;
    block-size: 12px;
    border-radius: var(--radius-pill);
    background-color: var(--color-white);
    transition: inset-inline-start 150ms;
  }

  .switch[data-on] .thumb {
    inset-inline-start: 14px;
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

  :global([data-theme='dark']) .switch {
    background-color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .switch .thumb {
    background-color: var(--color-gray-500);
  }

  :global([data-theme='dark']) .switch[data-on] {
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .switch[data-on] .thumb {
    background-color: var(--color-black);
  }

  :is(.icon, .switch):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
