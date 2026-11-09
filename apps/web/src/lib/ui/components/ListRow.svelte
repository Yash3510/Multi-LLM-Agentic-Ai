<script lang="ts">
  // One row of a list (layout look §4.4, §9.2), as the running app draws it: gray-100 on hover in
  // the side list (gray-50 at 70 % in list dialogs) and a 3.5 % black fill on the open item. A link when it opens something; otherwise a
  // plain row, so actions inside it stay their own buttons.
  import { appHref } from '$lib/ui/app-href';
  import type { PathnameWithSearchOrHash } from '$app/types';
  import type { Snippet } from 'svelte';

  type Props = {
    /** An app path; resolved against the base path, as Link does. */
    href?: PathnameWithSearchOrHash;
    /** The item open beside the list. */
    current?: boolean;
    /** `sidebar`: 32 px rows at 13 px, radius 12. `dialog`: 14 px rows, radius 8. */
    variant?: 'sidebar' | 'dialog';
    /** For a plain row inside a table, `row`; its cells then carry `cell`. */
    role?: 'row';
    children: Snippet;
  };

  let { href, current = false, variant = 'dialog', role, children }: Props = $props();
</script>

{#if href}
  <a
    href={appHref(href)}
    data-list-row
    data-variant={variant}
    data-current={current ? '' : undefined}
    aria-current={current ? 'page' : undefined}
  >
    {@render children()}
  </a>
{:else}
  <div {role} data-list-row data-variant={variant} data-current={current ? '' : undefined}>
    {@render children()}
  </div>
{/if}

<style>
  [data-list-row] {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-2);
    inline-size: 100%;
    min-inline-size: 0;
    color: inherit;
    white-space: nowrap;
    text-decoration: none;
    transition: background-color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  [data-list-row][data-variant='sidebar'] {
    /* 11 px sides and no gap: the run marker's 20 px slot lines titles up at 37 px (measured). */
    gap: 0;
    padding: 6px 11px;
    border-radius: var(--radius-inset);
    font-size: var(--text-small);
    line-height: var(--text-small--line-height);
  }

  [data-list-row][data-variant='dialog'] {
    padding: var(--spacing-2) var(--spacing-3);
    border-radius: 8px;
    font-size: var(--text-ui);
    line-height: var(--text-ui--line-height);
  }

  /* Touch screens get no hover fill (layout look §4.4). */
  @media (hover: hover) {
    [data-list-row][data-variant='sidebar']:hover {
      background-color: var(--color-row-hover);
    }

    [data-list-row][data-variant='dialog']:hover {
      background-color: color-mix(in srgb, var(--color-gray-50) 70%, transparent);
    }

    :global([data-theme='dark']) [data-list-row][data-variant='dialog']:hover {
      background-color: color-mix(in srgb, var(--color-gray-850) 50%, transparent);
    }
  }

  [data-list-row][data-current] {
    background-color: var(--color-row-current);
  }

  [data-list-row]:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }
</style>
