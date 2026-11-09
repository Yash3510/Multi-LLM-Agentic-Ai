<script lang="ts">
  // One skill in the list (workspace look §7.1, F102): name, id and age with Inactive and Read
  // Only badges, the description under it, the owner, then the more menu and the switch, shown
  // only to those who may change it. While Shift is held the controls become one delete button.
  import type { Skill } from '$lib/data';
  import { ago, longDate } from '$lib/ui/ago';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Menu from './Menu.svelte';
  import Switch from './Switch.svelte';

  type Props = {
    skill: Skill;
    quick: boolean;
    onopen?: (id: string) => void;
    ontoggle?: (id: string, active: boolean) => void;
    onclone?: (skill: Skill) => void;
    onexport?: (skill: Skill) => void;
    ondelete?: (id: string) => void;
    onconfirmdelete?: (skill: Skill) => void;
  };

  let { skill, quick, onopen, ontoggle, onclone, onexport, ondelete, onconfirmdelete }: Props =
    $props();

  function open(event: Event) {
    if (event.target instanceof Element && event.target.closest('button, a, input, [role="menu"]'))
      return;
    onopen?.(skill.id);
  }

  function key(event: KeyboardEvent) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open(event);
  }

  const owner = $derived(
    skill.owner ? skill.owner.name.charAt(0).toUpperCase() + skill.owner.name.slice(1) : '',
  );
</script>

<div class="row" role="button" tabindex="0" onclick={open} onkeydown={key}>
  <div class="text">
    <div class="line">
      <span class="name" title={skill.id}>{skill.name}</span>
      <span class="command">/{skill.id}</span>
      <span class="age" title={longDate.format(skill.updated)}>{ago(skill.updated)}</span>
      {#if !skill.active}<span class="badge">Inactive</span>{/if}
      {#if !skill.writable}<span class="badge">Read Only</span>{/if}
    </div>
    {#if skill.description}<div class="content" title={skill.description}>
        {skill.description}
      </div>{/if}
  </div>
  {#if owner}<span class="owner" title={skill.owner?.email ?? 'Deleted User'}>{owner}</span>{/if}
  {#if skill.writable}
    <span class="controls">
      {#if quick}
        <button
          type="button"
          class="icon"
          aria-label="Delete"
          title="Delete"
          onclick={() => ondelete?.(skill.id)}><Icon name="trash" size={16} /></button
        >
      {:else}
        <span class="group">
          <Menu
            label="Skill Menu"
            backLabel="Back"
            align="end"
            items={[
              { id: 'edit', label: 'Edit', icon: 'rename', onSelect: () => onopen?.(skill.id) },
              { id: 'clone', label: 'Clone', icon: 'copy', onSelect: () => onclone?.(skill) },
              {
                id: 'export',
                label: 'Export',
                icon: 'download-simple',
                onSelect: () => onexport?.(skill),
              },
              { type: 'separator' },
              {
                id: 'delete',
                label: 'Delete',
                icon: 'trash',
                onSelect: () => onconfirmdelete?.(skill),
              },
            ]}
          >
            {#snippet trigger({ props })}
              <button {...props} class="icon" aria-label="Skill Menu" title="More"
                ><Icon name="dots-three" size={16} /></button
              >
            {/snippet}
          </Menu>
          <Switch on={skill.active} onchange={(on) => ontoggle?.(skill.id, on)} />
        </span>
      {/if}
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
