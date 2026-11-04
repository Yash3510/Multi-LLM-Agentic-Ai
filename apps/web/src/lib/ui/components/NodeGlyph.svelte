<script lang="ts" module>
  export type NodeState = 'done' | 'released' | 'withheld' | 'interrupted';
</script>

<script lang="ts">
  // The node glyph (own-4ce look S4), drawn still: a ring on a 14-unit grid with its mark. Used
  // as the sidebar run marker (12 px) and on the stage rail (14 px). The live states (waiting,
  // working, closing) come with the answer stream.
  type Props = { state: NodeState; size?: number; label?: string };

  let { state, size = 12, label }: Props = $props();
</script>

<svg
  viewBox="0 0 14 14"
  width={size}
  height={size}
  class="node"
  data-state={state}
  role={label ? 'img' : undefined}
  aria-label={label}
  aria-hidden={label ? undefined : true}
>
  <circle class="ring" cx="7" cy="7" r="5.2" />
  {#if state === 'released'}
    <path class="mark" d="M4.6 7.2l1.5 1.5 3-3.3" />
  {:else if state === 'withheld' || state === 'interrupted'}
    <path class="mark" d="M4.8 7h4.4" />
  {:else}
    <circle class="dot" cx="7" cy="7" r="1.9" />
  {/if}
</svg>

<style>
  .node {
    flex-shrink: 0;
    overflow: visible;
    --node-ink: var(--color-gray-900);
    --node-done: var(--color-gray-700);
    --node-amber: var(--color-amber-500);
  }

  :global([data-theme='dark']) .node {
    --node-ink: var(--color-white);
    --node-done: var(--color-gray-300);
    --node-amber: var(--color-amber-400);
  }

  .ring {
    fill: none;
    stroke: var(--node-done);
    stroke-width: 1.25;
    stroke-linecap: round;
  }

  .dot {
    fill: var(--node-done);
  }

  .mark {
    fill: none;
    stroke: var(--node-ink);
    stroke-width: 1.35;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .node:is([data-state='released'], [data-state='withheld']) .ring {
    stroke: var(--node-ink);
  }

  .node[data-state='interrupted'] :is(.ring, .mark) {
    stroke: var(--node-amber);
  }
</style>
