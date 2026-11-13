<script lang="ts">
  // An admin section's frame (admin look §4, §13a): the tab strip with counts beside the
  // scrolling content; a column below 1024 px, a row from there.
  import type { PathnameWithSearchOrHash } from '$app/types';
  import type { Snippet } from 'svelte';
  import { appHref } from '$lib/ui/app-href';

  type Item = { href: PathnameWithSearchOrHash; label: string; count?: number; current: boolean };
  type Props = {
    label: string;
    items: Item[];
    children: Snippet;
    /** Evaluations' pane has 16 px sides where People's has 14. */
    roomy?: boolean;
  };

  let { label, items, children, roomy = false }: Props = $props();
</script>

<div class="section-shell">
  <nav class="tabs" aria-label={label}>
    {#each items as item (item.href)}
      <a
        href={appHref(item.href)}
        aria-current={item.current ? 'page' : undefined}
        draggable="false"
        >{item.label}{#if item.count !== undefined}<span class="count"
            >{item.count.toLocaleString()}</span
          >{/if}</a
      >
    {/each}
  </nav>
  <div class="pane" class:roomy>{@render children()}</div>
</div>

<style>
  .section-shell {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    block-size: 100%;
    padding-block-end: 8px;
  }

  @media (min-width: 64rem) {
    .section-shell {
      flex-direction: row;
    }
  }

  .tabs {
    display: flex;
    gap: 10px;
    margin-inline: 8px;
    padding-inline: 8px;
    overflow-x: auto;
    scrollbar-width: none;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  @media (min-width: 40rem) {
    .tabs {
      margin-inline: 10px;
    }
  }

  @media (min-width: 64rem) {
    .tabs {
      flex: none;
      flex-direction: column;
      gap: 0;
      inline-size: 200px;
      margin: 0;
      padding-inline: 10px;
    }
  }

  :global([data-theme='dark']) .tabs {
    color: var(--color-gray-200);
  }

  .tabs a {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    padding: 4px 2px;
    border-radius: 8px;
    color: var(--color-gray-300);
    user-select: none;
    transition: color 150ms;
  }

  .tabs a:hover {
    color: var(--color-gray-700);
  }

  .tabs a[aria-current] {
    color: inherit;
  }

  :global([data-theme='dark']) .tabs a {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .tabs a:hover {
    color: var(--color-white);
  }

  :global([data-theme='dark']) .tabs a[aria-current] {
    color: inherit;
  }

  .count {
    opacity: 0.6;
  }

  .tabs a:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }

  .pane {
    flex: 1;
    padding-inline: 14px;
    overflow-y: scroll;
  }

  @media (min-width: 64rem) {
    .pane {
      padding-inline: 0 16px;
    }
  }
  .pane.roomy {
    padding-inline: 16px;
  }

  @media (min-width: 64rem) {
    .pane.roomy {
      padding-inline: 0 16px;
    }
  }
</style>
