<script lang="ts">
  // The sources under an answer (chat-messages look §7.1): a row that counts them and opens the
  // list, each with its citation number. It lines up with the provenance rows above it.
  import type { Source } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';

  let { sources, onopen }: { sources: Source[]; onopen?: (index: number) => void } = $props();

  let open = $state(false);
  const count = $derived(sources.length);
</script>

<div class="bar">
  <button
    type="button"
    class="toggle"
    aria-label={count === 1 ? 'Toggle 1 source' : `Toggle ${count} sources`}
    aria-expanded={open}
    onclick={() => (open = !open)}
  >
    <span class="n">{count}</span>
    {count === 1 ? 'Source' : 'Sources'}
    <span class="caret" data-open={open ? '' : undefined}
      ><Icon name="sort-caret-down" size={12} /></span
    >
  </button>
  {#if open}
    <ul class="list">
      {#each sources as source (source.index)}
        <li>
          <button
            type="button"
            class="item"
            aria-label="View source: {source.title}"
            onclick={() => onopen?.(source.index)}
          >
            <span class="badge">{source.index}</span>
            <span class="title">{source.title}</span>
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .bar {
    display: flex;
    flex-direction: column;
    border-block-start: 1px solid var(--color-gray-50);
  }

  :global([data-theme='dark']) .bar {
    border-color: var(--color-gray-850);
  }

  /* Polish pass (WP-F-10): a row like the provenance folds above, a hairline over it, the count
     in Plex Mono and the same caret. */
  .toggle {
    align-self: flex-start;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    min-block-size: 34px;
    color: var(--color-gray-600);
    font-size: var(--text-small);
    transition: color 150ms;
  }

  .toggle:hover {
    color: var(--color-gray-900);
  }

  .n {
    color: var(--color-gray-900);
    font-family: var(--font-mono);
    font-size: 11.5px;
  }

  .caret {
    display: inline-flex;
    color: var(--color-gray-400);
    transition: rotate 300ms;
  }

  .caret[data-open] {
    rotate: 180deg;
  }

  :global([data-theme='dark']) .toggle {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) :is(.toggle:hover, .n) {
    color: var(--color-gray-100);
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
    padding-block: 6px;
    font-size: var(--text-caption);
  }

  .item {
    display: flex;
    gap: 6px;
    inline-size: 100%;
    border-radius: var(--radius-inset);
    color: var(--color-gray-600);
    text-align: start;
  }

  :global([data-theme='dark']) .item {
    color: var(--color-gray-300);
  }

  .badge {
    padding-inline: var(--spacing-1);
    border-radius: 6px;
    background-color: var(--color-gray-50);
  }

  :global([data-theme='dark']) .badge {
    background-color: var(--color-gray-850);
  }

  .title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: color 150ms;
  }

  .item:hover .title {
    color: var(--color-black);
  }

  :global([data-theme='dark']) .item:hover .title {
    color: var(--color-white);
  }

  :is(.toggle, .item):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }
</style>
