<script lang="ts">
  // The stage rail (own-4ce look S3, features F19-F24): five nodes, Planner to the person's gate,
  // with each stage's time and note, the wires between them and the re-plan arc. Derived only
  // from the run's events, so a reloaded chat draws it as it ended. Still planned: the light that
  // travels between nodes on a live run, the release sweep and the arc's spark.
  import {
    deriveRun,
    formatStageTime,
    RAIL,
    type RailStage,
    type StageState,
  } from '$lib/data/stages';
  import type { StreamEvent } from '$lib/data';
  import NodeGlyph, { type NodeState } from './NodeGlyph.svelte';

  type Props = {
    events: StreamEvent[];
    finished: boolean;
    /** The clock to measure a running stage against; ticks on its own while the run is live. */
    now?: number;
  };

  let { events, finished, now }: Props = $props();

  let clock = $state(Date.now());
  const run = $derived(deriveRun(events, finished, now ?? clock));

  // The running stage's time counts up every 100 ms, only while something runs (F20).
  $effect(() => {
    if (!run.running || now !== undefined) return;
    const timer = setInterval(() => (clock = Date.now()), 100);
    return () => clearInterval(timer);
  });

  const NAMES: Record<RailStage, string> = {
    planner: 'Planner',
    analyst: 'Analyst',
    author: 'Author',
    challenger: 'Challenger',
    'sign-off': 'You',
  };

  const LOOK: Record<StageState, NodeState> = {
    pending: 'waiting',
    requeued: 'requeued',
    skipped: 'skipped',
    active: 'working',
    done: 'done',
    fail: 'fail',
    interrupted: 'interrupted',
    released: 'released',
    withheld: 'withheld',
  };

  const reached = (state: StageState) => !['pending', 'skipped', 'requeued'].includes(state);

  /** The wire after a node: filled once the next node is reached; into the gate, ink once the
   * person decided, amber when the run was cut off before they did. */
  function wire(index: number): 'future' | 'done' | 'released' | 'held' {
    const next = run.stages[RAIL[index + 1]];
    if (RAIL[index + 1] === 'sign-off') {
      if (next.state === 'released' || next.state === 'withheld') return 'released';
      if (finished && next.state === 'interrupted') return 'held';
    }
    return reached(next.state) ? 'done' : 'future';
  }

  function time(stage: RailStage): string {
    const view = run.stages[stage];
    if (!reached(view.state) || view.ms <= 0) return '';
    const text = formatStageTime(view.ms);
    return stage === 'sign-off' && (view.state === 'released' || view.state === 'withheld')
      ? `waited ${text}`
      : text;
  }

  const ORDINAL = (n: number) => {
    const tens = n % 100;
    if (tens >= 11 && tens <= 13) return `${n}th`;
    return `${n}${['th', 'st', 'nd', 'rd'][n % 10] ?? 'th'}`;
  };
</script>

{#if run.rail}
  <div class="rail" data-replanned={run.replans > 0 ? '' : undefined}>
    <ol class="row" aria-label="Agent chain">
      {#each RAIL as stage, index (stage)}
        {@const view = run.stages[stage]}
        {@const timeText = time(stage)}
        <li class="column" data-stage={stage} data-state={view.state}>
          <button
            type="button"
            class="node"
            disabled={run.running || view.state === 'skipped'}
            aria-label={[
              NAMES[stage],
              view.passes > 1 ? `ran ${view.passes} times` : '',
              timeText,
              view.note ?? '',
            ]
              .filter(Boolean)
              .join(', ')}
          >
            <NodeGlyph state={LOOK[view.state]} size={14} />
            <span class="name"
              >{NAMES[
                stage
              ].toUpperCase()}{#if view.passes > 1 && stage !== 'planner' && stage !== 'sign-off'}<span
                  class="passes">×{view.passes}</span
                >{/if}</span
            >
            <span class="time">{timeText || ' '}</span>
            <span class="note">{view.note ?? ' '}</span>
          </button>
          {#if index < RAIL.length - 1}
            <span class="wire" data-wire={wire(index)} aria-hidden="true"
              ><span class="fill"></span></span
            >
          {/if}
        </li>
      {/each}
    </ol>
    {#if run.replans > 0}
      <div class="arc" aria-hidden="true">
        <svg viewBox="0 0 100 22" preserveAspectRatio="none">
          <path d="M100 22 C86 1 14 1 0 22" />
        </svg>
        <span class="arc-label">CHALLENGER sent it back · {ORDINAL(run.replans + 1)} try</span>
      </div>
      <span class="sr-only">
        The Challenger sent the draft back {run.replans === 1 ? 'once' : `${run.replans} times`};
        Analyst, Author and Challenger ran again. This is the {ORDINAL(run.replans + 1)} try.
      </span>
    {/if}
  </div>
{/if}

<style>
  .rail {
    position: relative;
    inline-size: 100%;
    max-inline-size: 34rem;
    margin-block-end: var(--spacing-3);
    padding-block-start: 10px;
    --wire: var(--color-gray-300);
    --charged: var(--color-gray-400);
    --held: var(--color-amber-400);
    --released-ink: var(--color-gray-900);
    --name-base: var(--color-gray-600);
  }

  :global([data-theme='dark']) .rail {
    --wire: var(--color-gray-700);
    --charged: var(--color-gray-600);
    --held: var(--color-amber-600);
    --released-ink: var(--color-white);
    --name-base: var(--color-gray-300);
  }

  .rail[data-replanned] {
    padding-block-start: 36px;
  }

  .row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
  }

  .column {
    position: relative;
  }

  .node {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-inline: -4px;
    padding-inline: 4px;
    border-radius: 8px;
    text-align: start;
    color: var(--label);
    --label: var(--color-gray-500);
  }

  .node:disabled {
    cursor: default;
  }

  .node:focus-visible {
    outline: none;
    box-shadow:
      0 0 0 1px var(--color-gray-400),
      var(--shadow-focus);
  }

  /* Label colours by state (look S3.1). */
  .column[data-state='done'] .node,
  .column[data-state='withheld'] .node {
    --label: var(--color-gray-800);
  }

  .column:is([data-state='active'], [data-state='released']) .node {
    --label: var(--color-gray-900);
  }

  .column[data-state='skipped'] .node {
    --label: var(--color-gray-300);
  }

  .column:is([data-state='fail'], [data-state='interrupted']) .node {
    --label: var(--color-amber-700);
  }

  :global([data-theme='dark']) .column:is([data-state='done'], [data-state='withheld']) .node {
    --label: var(--color-gray-100);
  }

  :global([data-theme='dark']) .column:is([data-state='active'], [data-state='released']) .node {
    --label: var(--color-white);
  }

  :global([data-theme='dark']) .column[data-state='requeued'] .node {
    --label: var(--color-gray-400);
  }

  :global([data-theme='dark']) .column[data-state='skipped'] .node {
    --label: var(--color-gray-600);
  }

  :global([data-theme='dark']) .column:is([data-state='fail'], [data-state='interrupted']) .node {
    --label: var(--color-yellow-300);
  }

  .name {
    margin-block-start: var(--spacing-2);
    font-size: var(--text-tag);
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    line-height: 15.75px;
    white-space: nowrap;
    transition: color 700ms;
  }

  .passes {
    margin-inline-start: var(--spacing-1);
    font-weight: var(--font-weight-normal);
    letter-spacing: 0;
    opacity: 0.7;
  }

  .time,
  .note {
    display: block;
    font-size: var(--text-tag);
    font-variant-numeric: tabular-nums;
    line-height: 1.25;
  }

  :global([data-theme='dark']) :is(.time, .note) {
    opacity: 0.75;
  }

  /* Wires (look S3.3): a dashed hairline from 18 px in to 4 px before the column's end, at the
     ring's centre, with a solid fill over it by state. */
  .wire {
    position: absolute;
    inset-block-start: calc(10px + 7px);
    inset-inline: 18px 4px;
    block-size: 0;
    border-block-start: 1px dashed var(--wire);
  }

  .rail[data-replanned] .wire {
    inset-block-start: calc(36px + 7px);
  }

  .fill {
    position: absolute;
    inset: -1px 0 auto;
    block-size: 1px;
    transform: scaleX(0);
    transform-origin: left;
    transition: background-color 800ms ease;
  }

  .wire:not([data-wire='future']) .fill {
    transform: scaleX(1);
  }

  .wire[data-wire='done'] .fill {
    background-color: var(--charged);
  }

  .wire[data-wire='released'] .fill {
    background-color: var(--released-ink);
  }

  .wire[data-wire='held'] .fill {
    background-color: var(--held);
  }

  /* The re-plan arc (look S3.4): over the Analyst to Author columns, 22 px tall, dashed amber. */
  .arc {
    position: absolute;
    inset-block-start: 14px;
    inset-inline: calc(20% + 7px) calc(20% + 7px - 14px);
    block-size: 22px;
  }

  .arc svg {
    inline-size: 100%;
    block-size: 100%;
    overflow: visible;
  }

  .arc path {
    fill: none;
    stroke: var(--color-amber-400);
    stroke-width: 1.5;
    stroke-dasharray: 4 3;
    vector-effect: non-scaling-stroke;
  }

  :global([data-theme='dark']) .arc path {
    stroke: var(--color-amber-600);
  }

  .arc-label {
    position: absolute;
    inset-block-start: -10px;
    inset-inline-start: 50%;
    translate: -50% 0;
    color: var(--color-amber-700);
    font-size: 10px;
    letter-spacing: 0.025em;
    line-height: 15px;
    white-space: nowrap;
  }

  :global([data-theme='dark']) .arc-label {
    color: var(--color-yellow-300);
  }
</style>
