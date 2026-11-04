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
  import { untrack } from 'svelte';

  // The node glyph (own-4ce look S4): a ring on a 14-unit grid. Waiting is six dashes, working is
  // six dots with a violet light running round them, and the finished looks close the ring with
  // their mark. Used on the stage rail (14 px) and as the sidebar run marker (12 px).
  type Props = {
    state: NodeState;
    size?: number;
    label?: string;
    /** Bumped on each landing: one soft ring grows and fades (look S4). */
    bloom?: number;
  };

  let { state, size = 12, label, bloom = 0 }: Props = $props();

  // A node that mounts finished is drawn complete; one that finishes in front of the reader
  // plays the close (look S4): dots stretch into the ring, the centre or the mark draws in.
  const FINISHED = ['done', 'fail', 'interrupted', 'released', 'withheld'];
  const initial = untrack(() => state);
  const fresh = $derived(state !== initial && FINISHED.includes(state));

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
  data-fresh={fresh ? '' : undefined}
  role={label ? 'img' : undefined}
  aria-label={label}
  aria-hidden={label ? undefined : true}
>
  {#if bloom > 0}
    {#key bloom}<circle class="bloom" cx="7" cy="7" r="5.2" />{/key}
  {/if}
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
    {#key state}
      <circle class="ring" cx="7" cy="7" r="5.2" pathLength="6" />
      {#if state === 'released'}
        <path class="mark" d="M4.6 7.2l1.5 1.5 3-3.3" pathLength="1" />
      {:else if state === 'withheld' || state === 'interrupted'}
        <path class="mark" d="M4.8 7h4.4" pathLength="1" />
      {:else}
        <circle class="dot" cx="7" cy="7" r="1.9" />
      {/if}
    {/key}
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

  .bloom {
    fill: none;
    stroke: var(--node-lit);
    stroke-width: 1;
    vector-effect: non-scaling-stroke;
    animation: bloom 1.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  }

  /* The ring grows to 1.8 times its radius (5.2 to 9.36) by its radius, not a scale. */
  @keyframes bloom {
    from {
      opacity: 0.45;
      r: 5.2px;
    }
    to {
      opacity: 0;
      r: 9.36px;
    }
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

  /* The close (look S4): six round dots fade in by 30 %, then stretch into the ring as it thins;
     the centre dot grows in after 450 ms; a mark draws in after 1.1 s. */
  .node[data-fresh] .ring {
    animation: close 1.4s cubic-bezier(0.65, 0, 0.35, 1) both;
  }

  .node[data-fresh] .dot {
    transform-origin: 7px 7px;
    animation: core 1s cubic-bezier(0.65, 0, 0.35, 1) 450ms both;
  }

  .node[data-fresh] .mark {
    stroke-dasharray: 1;
    animation: draw 900ms cubic-bezier(0.45, 0, 0.2, 1) 1.1s both;
  }

  @keyframes close {
    0% {
      opacity: 0;
      stroke-width: 2.4;
      stroke-dasharray: 0 1;
    }
    30% {
      opacity: 1;
      stroke-width: 2.4;
      stroke-dasharray: 0 1;
    }
    100% {
      stroke-width: 1.25;
      stroke-dasharray: 1 0;
    }
  }

  @keyframes core {
    from {
      opacity: 0;
      scale: 0.5;
    }
  }

  @keyframes draw {
    from {
      stroke-dashoffset: 1;
    }
    to {
      stroke-dashoffset: 0;
    }
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

    .bloom {
      display: none;
    }

    .node[data-fresh] :is(.ring, .dot, .mark) {
      animation: none;
    }
  }
</style>
