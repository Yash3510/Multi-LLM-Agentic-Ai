<script lang="ts">
  // The sources under an answer (chat-messages look §7.1): a pill that counts them and opens the
  // list, each with its citation number.
  import type { Source } from '$lib/data';

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
    {count === 1 ? '1 Source' : `${count} Sources`}
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
    margin-inline: -2px;
    padding-block: var(--spacing-1);
  }

  .toggle {
    align-self: flex-start;
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    block-size: 32px;
    padding-inline: 14px;
    border: 1px solid color-mix(in srgb, var(--color-gray-50) 30%, transparent);
    border-radius: var(--radius-pill);
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    transition: background-color 150ms;
  }

  .toggle:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .toggle {
    border-color: color-mix(in srgb, var(--color-gray-850) 30%, transparent);
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .toggle:hover {
    background-color: var(--color-gray-800);
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
