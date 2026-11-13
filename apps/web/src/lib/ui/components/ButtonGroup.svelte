<script lang="ts">
  // Related actions as one labelled group. Spaced by default: one leading-aligned row under the
  // content it acts on, primary first, wrapping only when the room runs out. `attached` joins them
  // into one strip, squaring the inner corners and sharing the edges between neighbours.
  import type { Snippet } from 'svelte';
  import type { HTMLAttributes } from 'svelte/elements';

  type Props = HTMLAttributes<HTMLDivElement> & {
    /** Names the group for assistive technology. */
    label: string;
    attached?: boolean;
    children: Snippet;
  };

  let { label, attached = false, children, class: className, ...rest }: Props = $props();
</script>

<div role="group" aria-label={label} class={['actions', { attached }, className]} {...rest}>
  {@render children()}
</div>

<style>
  .actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: flex-start;
    gap: var(--spacing-2);
  }

  .attached {
    display: inline-flex;
    flex-wrap: nowrap;
    gap: 0;
  }

  .attached > :global([data-action]:not(:first-child)) {
    margin-inline-start: -1px;
    border-start-start-radius: 0;
    border-end-start-radius: 0;
  }

  .attached > :global([data-action]:not(:last-child)) {
    border-start-end-radius: 0;
    border-end-end-radius: 0;
  }

  /* The shared edge belongs to whichever neighbour is hovered, focused or selected. */
  .attached > :global([data-action]:is(:hover, :focus-visible, [aria-pressed='true'])) {
    z-index: 1;
  }
</style>
