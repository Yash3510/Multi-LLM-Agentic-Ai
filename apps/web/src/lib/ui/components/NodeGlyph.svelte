<script lang="ts" module>
  export type NodeState =
    | 'waiting'
    | 'requeued'
    | 'skipped'
    | 'working'
    | 'done'
    | 'fail'
    | 'interrupted'
    | 'released'
    | 'withheld';
</script>

<script lang="ts">
  // The node glyph (own-4ce look S4): a ring on a 14-unit grid. Waiting is six dashes, working is
  // six dots with a violet light running round them, and the finished looks close the ring with
  // their mark. Used on the stage rail (14 px) and as the sidebar run marker (12 px).
  type Props = { state: NodeState; size?: number; label?: string };

  let { state, size = 12, label }: Props = $props();

  // Six positions on the ring, from the top, every 60 degrees clockwise.
  const DOTS = Array.from({ length: 6 }, (_, index) => {
    const angle = (index * Math.PI) / 3 - Math.PI / 2;
    return { x: 7 + 5.2 * Math.cos(angle), y: 7 + 5.2 * Math.sin(angle) };
  });
  // A dash is 1/15 of the ring; six of them sit where the working dots do.
  const CIRCUMFERENCE = 2 * Math.PI * 5.2;
  const DASH = CIRCUMFERENCE / 15;
  const GAP = CIRCUMFERENCE / 6 - DASH;
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
  {#if state === 'waiting' || state === 'requeued' || state === 'skipped'}
    <circle
      class="dashes"
      cx="7"
      cy="7"
      r="5.2"
      stroke-dasharray="{DASH} {GAP}"
      stroke-dashoffset={DASH / 2}
      transform="rotate(-90 7 7)"
    />
  {:else if state === 'working'}
    {#each DOTS as dot, index (index)}
      <circle
        class="light"
        cx={dot.x}
        cy={dot.y}
        r="1.2"
        style:animation-delay="{index * 0.283}s"
      />
    {/each}
    <circle class="hub" cx="7" cy="7" r="1" />
  {:else}
    <circle class="ring" cx="7" cy="7" r="5.2" />
    {#if state === 'released'}
      <path class="mark" d="M4.6 7.2l1.5 1.5 3-3.3" />
    {:else if state === 'withheld' || state === 'interrupted'}
      <path class="mark" d="M4.8 7h4.4" />
    {:else}
      <circle class="dot" cx="7" cy="7" r="1.9" />
    {/if}
  {/if}
</svg>

<style>
  .node {
    flex-shrink: 0;
    overflow: visible;
    --node-ink: var(--color-gray-900);
    --node-done: var(--color-gray-700);
    --node-wait: var(--color-gray-300);
    --node-requeued: var(--color-gray-500);
    --node-amber: var(--color-amber-500);
    --node-working: var(--color-violet-500);
    --node-lit: var(--color-violet-600);
  }

  :global([data-theme='dark']) .node {
    --node-ink: var(--color-white);
    --node-done: var(--color-gray-300);
    --node-wait: var(--color-gray-700);
    --node-amber: var(--color-amber-400);
    --node-working: var(--color-violet-400);
    --node-lit: var(--color-violet-200);
  }

  .dashes {
    fill: none;
    stroke: var(--node-wait);
    stroke-width: 1;
  }

  .node[data-state='requeued'] .dashes {
    stroke: var(--node-requeued);
  }

  .node[data-state='skipped'] {
    opacity: 0.5;
  }

  .light {
    fill: var(--node-working);
    opacity: 0.4;
    animation: lap 1.7s ease-in-out infinite;
  }

  .hub {
    fill: var(--node-lit);
  }

  .ring {
    fill: none;
    stroke: var(--node-done);
    stroke-width: 1.25;
    stroke-linecap: round;
    transition: stroke 300ms;
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

  .node:is([data-state='fail'], [data-state='interrupted']) .ring {
    stroke: var(--node-amber);
  }

  .node[data-state='fail'] .dot {
    fill: var(--node-amber);
  }

  .node[data-state='interrupted'] .mark {
    stroke: var(--node-amber);
  }

  /* Each dot in turn takes the lit colour at full strength, then settles back (look S4). */
  @keyframes lap {
    0% {
      fill: var(--node-lit);
      opacity: 1;
    }
    35% {
      opacity: 0.7;
    }
    70%,
    100% {
      fill: var(--node-working);
      opacity: 0.4;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .light {
      animation: none;
      opacity: 0.7;
    }
  }
</style>
