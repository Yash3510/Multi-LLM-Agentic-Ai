<script lang="ts">
  // A shortcut drawn as keycaps: keys={['mod', 'k']} shows ⌘ K on Apple platforms and Ctrl K
  // elsewhere. Nested <kbd> per HTML for a key combination; symbols carry a spoken name. Inside a
  // control, hide it (aria-hidden) and give the control aria-keyshortcuts instead.
  import type { HTMLAttributes } from 'svelte/elements';
  import { isApple, keycap } from './keycap';

  let {
    keys,
    class: className,
    ...rest
  }: HTMLAttributes<HTMLElement> & { keys: string[] } = $props();

  const apple = isApple();
  const caps = $derived(keys.map((key) => keycap(key, apple)));
</script>

<kbd class={['inline-flex items-center gap-0.5 align-middle font-sans', className]} {...rest}>
  {#each caps as cap, index (index)}
    {#if index > 0}<span class="sr-only">+</span>{/if}
    <kbd class="cap text-caption font-medium text-ink-2 tabular">
      {#if cap.spoken}
        <span aria-hidden="true">{cap.legend}</span><span class="sr-only">{cap.spoken}</span>
      {:else}
        {cap.legend}
      {/if}
    </kbd>
  {/each}
</kbd>

<style>
  /* The composer's send-hint key cap (own-4ce look S16): 11 px on a grey face, radius 5 px. */
  .cap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 1px var(--spacing-1);
    border-radius: 5px;
    background-color: var(--color-gray-100);
    color: var(--color-gray-600);
    font-family: inherit;
    font-size: 11px;
    line-height: var(--text-micro--line-height);
    white-space: nowrap;
  }

  :global([data-theme='dark']) .cap {
    background-color: var(--color-gray-800);
    color: var(--color-gray-300);
  }

  /* Inside a button the caps take the button's own ink, so they read on the solid pill too. */
  :global([data-action]) .cap {
    background-color: color-mix(in srgb, currentColor 12%, transparent);
    color: inherit;
  }
</style>
