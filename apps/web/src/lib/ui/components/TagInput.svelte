<script lang="ts">
  // Tags (workspace look §3.2): chips that remove on press, then a field where Enter or Space adds
  // one. Read-only shows plain chips.
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = { tags: string[]; disabled?: boolean };

  let { tags = $bindable(), disabled = false }: Props = $props();

  let tag = $state('');

  function add(event: KeyboardEvent) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    const name = tag.trim();
    if (name && !tags.includes(name)) tags = [...tags, name];
    tag = '';
  }
</script>

<div class="tags">
  {#each tags as name (name)}
    {#if disabled}
      <span class="tag"><span class="truncate">{name}</span></span>
    {:else}
      <button type="button" class="tag" onclick={() => (tags = tags.filter((one) => one !== name))}
        ><span class="truncate">{name}</span><Icon name="x-bold" size={12} /></button
      >
    {/if}
  {/each}
  {#if !disabled}
    <input
      class="tag-input"
      class:after={tags.length > 0}
      bind:value={tag}
      onkeydown={add}
      placeholder="Add a tag..."
      aria-label="Add a tag"
    />
  {/if}
</div>

<style>
  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    inline-size: 100%;
  }

  .tag {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 1px 6px;
    border: 1px solid var(--color-gray-100);
    border-radius: var(--radius-pill);
    background-color: color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: background-color 150ms;
  }

  button.tag:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .tag {
    border-color: var(--color-gray-800);
    background-color: color-mix(in srgb, var(--color-gray-800) 50%, transparent);
    color: var(--color-gray-300);
  }

  .tag-input {
    flex: 1;
    min-inline-size: 96px;
    background: transparent;
    color: inherit;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .tag-input.after {
    padding-inline: 2px;
  }

  .tag-input:focus {
    outline: none;
  }

  .tag-input::placeholder {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .tag-input::placeholder {
    color: var(--color-gray-500);
  }
</style>
