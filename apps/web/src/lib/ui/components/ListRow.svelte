<script lang="ts">
  // One row of a list (layout look §4.4, §9.2): a soft rectangle that takes the faint tint on
  // hover and a firmer tint when it is the open item. A link when it opens something; otherwise a
  // plain row, so actions inside it stay their own buttons.
  import { resolve } from '$app/paths';
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
    href={resolve(href)}
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
    padding: 6px var(--spacing-2);
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
    [data-list-row]:hover {
      background-color: var(--color-tint);
    }
  }

  [data-list-row][data-current] {
    background-color: var(--color-tint);
    box-shadow: var(--shadow-hairline);
  }

  [data-list-row]:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }
</style>
