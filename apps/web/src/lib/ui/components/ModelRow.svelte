<script lang="ts">
  // One custom model in the workspace list (workspace look §2.3): avatar, name, id and age on the
  // first line, the description under it, the owner, then the more button and the switch. No
  // fill and no hover fill; a hidden model is at half strength.
  import type { WorkspaceModel } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Logomark from './Logomark.svelte';

  let { model }: { model: WorkspaceModel } = $props();

  const relative = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  const STEPS: [Intl.RelativeTimeFormatUnit, number][] = [
    ['year', 31_536_000],
    ['month', 2_592_000],
    ['day', 86_400],
    ['hour', 3600],
    ['minute', 60],
  ];
  const ago = (when: Date) => {
    const seconds = (when.getTime() - Date.now()) / 1000;
    const [unit, size] = STEPS.find(([, step]) => Math.abs(seconds) >= step) ?? ['second', 1];
    return relative.format(Math.round(seconds / size), unit);
  };
  const long = new Intl.DateTimeFormat('en', { dateStyle: 'full', timeStyle: 'short' });
  const description = $derived(model.description || model.base || 'No description');
</script>

<div
  class="row"
  data-hidden={model.hidden ? '' : undefined}
  data-writable={model.writable ? '' : undefined}
>
  <span class="avatar" data-off={model.enabled ? undefined : ''}>
    {#if model.avatar}<img
        src={model.avatar}
        alt=""
        width="28"
        height="28"
        loading="lazy"
      />{:else}<Logomark size={28} />{/if}
  </span>
  <div class="text">
    <div class="line">
      <span class="name" title={model.name}>{model.name}</span>
      <span class="id">{model.id}</span>
      <span class="age" title={long.format(model.updated)}>{ago(model.updated)}</span>
      {#if !model.writable}<span class="badge">Read Only</span>{/if}
    </div>
    <div class="description" title={description}>{description}</div>
  </div>
  {#if model.owner}
    <span class="owner" title={model.owner.email ?? 'Deleted User'}>
      {model.owner.name.charAt(0).toUpperCase() + model.owner.name.slice(1)}
    </span>
  {/if}
  <span class="controls">
    <button type="button" class="more" aria-label="More" title="More">
      <Icon name="dots-three" size={16} />
    </button>
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
    border-radius: var(--radius-inset);
    text-align: start;
  }

  /* Keyboard users reach Edit through the row's More button. */
  .row[data-writable] {
    cursor: pointer;
  }

  .row[data-hidden] {
    opacity: 0.5;
  }

  .avatar {
    display: inline-flex;
    margin-inline-end: 4px;
  }

  .avatar img {
    border-radius: 8px;
    object-fit: cover;
  }

  .avatar[data-off] {
    opacity: 0.5;
  }

  .text {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
  }

  .line {
    display: flex;
    gap: var(--spacing-2);
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

  .id,
  .age {
    flex-shrink: 0;
    overflow: hidden;
    font-size: var(--text-micro);
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .id {
    display: none;
    max-inline-size: 40%;
    color: var(--color-gray-500);
  }

  @media (min-width: 40rem) {
    .id {
      display: block;
    }
  }

  .age {
    color: var(--color-gray-400);
  }

  .badge {
    align-self: center;
    padding: 0 6px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-100);
    color: var(--color-gray-600);
    font-size: var(--text-nano);
    line-height: 16px;
  }

  .description {
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
    align-self: center;
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
    gap: 6px;
    margin-inline-start: var(--spacing-2);
  }

  .more {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    border-radius: 8px;
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) :is(.name) {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) :is(.age, .description) {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .more {
    color: var(--color-gray-500);
  }
</style>
