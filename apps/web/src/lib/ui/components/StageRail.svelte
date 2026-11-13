<script lang="ts">
  // The stage rail (own-4ce look S3, features F19-F24): five nodes, Planner to the person's gate,
  // with each stage's time and note, the wires between them and the re-plan arc. Derived only
  // from the run's events, so a reloaded chat draws it as it ended. On a live run the rail trails
  // the run one hop at a time (F21): the finished node closes, a light travels the wire, the next
  // node starts working with a landing bloom; a release sweeps light across the names (F23).
  import {
    deriveRun,
    formatStageTime,
    RAIL,
    type RailStage,
    type StageState,
  } from '$lib/data/stages';
  import type { StreamEvent } from '$lib/data';
  import { onDestroy, untrack } from 'svelte';
  import NodeGlyph, { type NodeState } from './NodeGlyph.svelte';

  type Props = {
    events: StreamEvent[];
    finished: boolean;
    /** The clock to measure a running stage against; ticks on its own while the run is live. */
    now?: number;
    /** Trail a live run one hop at a time (F21). Opened chats and reduced motion never do. */
    paced?: boolean;
    /** Told the role the light is travelling to, and undefined when it lands. */
    onhandover?: (role: RailStage | undefined) => void;
  };

  let { events, finished, now, paced = true, onhandover }: Props = $props();

  let clock = $state(Date.now());
  const run = $derived(deriveRun(events, finished, now ?? clock));

  // The running stage's time counts up every 100 ms, only while something runs (F20).
  $effect(() => {
    if (!run.running || now !== undefined) return;
    const timer = setInterval(() => (clock = Date.now()), 100);
    return () => clearInterval(timer);
  });

  // Pacing: an opened (finished) chat and reduced motion draw the rail as it is.
  const reduced =
    typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  const pacing = untrack(() => paced && !finished) && !reduced;

  // The run's frontier: the working stage, else the furthest one reached.
  const frontier = $derived.by(() => {
    const active = RAIL.findIndex((stage) => run.stages[stage].state === 'active');
    if (active >= 0) return active;
    return RAIL.findLastIndex((stage) => reached(run.stages[stage].state));
  });

  let shown = $state(-1);
  let phase = $state<'rest' | 'closing' | 'travel'>('rest');
  let blooms = $state<Record<number, number>>({});
  let sweep = $state(false);
  // Re-plans seen at first sight: only later ones send a spark along the arc (F22).
  const seenReplans = untrack(() => deriveRun(events, finished, now ?? Date.now()).replans);
  const timers: ReturnType<typeof setTimeout>[] = [];
  onDestroy(() => timers.forEach(clearTimeout));

  const land = (index: number) => (blooms[index] = (blooms[index] ?? 0) + 1);

  // One hop: the finished node closes (950 ms), the light travels (1900 ms), the next node
  // starts working with a bloom. Queued hops run back to back; a re-plan jumps straight back.
  $effect(() => {
    const target = frontier;
    const resting = phase === 'rest';
    if (!pacing) return;
    untrack(() => {
      if (shown < 0) shown = target;
      else if (target < shown) {
        shown = target;
        phase = 'rest';
        land(target);
      } else if (target > shown && resting) {
        phase = 'closing';
        timers.push(
          setTimeout(() => {
            phase = 'travel';
            onhandover?.(RAIL[shown + 1]);
          }, 950),
          setTimeout(() => {
            shown += 1;
            phase = 'rest';
            land(shown);
            onhandover?.(undefined);
          }, 2850),
        );
      }
    });
  });

  /** The state a node shows: beyond the light it still looks unreached. */
  const shownState = (index: number): StageState => {
    const actual = run.stages[RAIL[index]].state;
    if (!pacing || index <= shown) return actual;
    return 'pending';
  };

  // The release sweep plays once, when the gate turns released in front of the reader (F23).
  $effect(() => {
    if (!pacing || shownState(RAIL.length - 1) !== 'released') return;
    untrack(() => {
      sweep = true;
      timers.push(setTimeout(() => (sweep = false), 5800));
    });
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
  function wire(index: number): 'future' | 'travel' | 'done' | 'released' | 'held' {
    if (pacing && index === shown && phase === 'travel') return 'travel';
    if (pacing && index >= shown) return 'future';
    const next = run.stages[RAIL[index + 1]];
    if (RAIL[index + 1] === 'sign-off') {
      if (next.state === 'released' || next.state === 'withheld') return 'released';
      if (finished && next.state === 'interrupted') return 'held';
    }
    return reached(next.state) ? 'done' : 'future';
  }

  function time(stage: RailStage, state: StageState): string {
    const view = run.stages[stage];
    if (!reached(state) || view.ms <= 0) return '';
    const text = formatStageTime(view.ms);
    return stage === 'sign-off' && (state === 'released' || state === 'withheld')
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
  <div
    class="rail"
    data-replanned={run.replans > 0 ? '' : undefined}
    data-sweep={sweep ? '' : undefined}
  >
    <ol class="row" aria-label="Agent chain">
      {#each RAIL as stage, index (stage)}
        {@const view = run.stages[stage]}
        {@const state = shownState(index)}
        {@const timeText = time(stage, state)}
        <li class="column" data-stage={stage} data-state={state} style:--index={index}>
          <button
            type="button"
            class="node"
            disabled={run.running || state === 'skipped'}
            aria-label={[
              NAMES[stage],
              view.passes > 1 ? `ran ${view.passes} times` : '',
              timeText,
              reached(state) ? (view.note ?? '') : '',
            ]
              .filter(Boolean)
              .join(', ')}
          >
            <NodeGlyph state={LOOK[state]} size={14} bloom={blooms[index] ?? 0} />
            <span class="name"
              >{NAMES[
                stage
              ].toUpperCase()}{#if view.passes > 1 && stage !== 'planner' && stage !== 'sign-off'}<span
                  class="passes">×{view.passes}</span
                >{/if}</span
            >
            <span class="time">{timeText || ' '}</span>
            <span class="note">{(reached(state) && view.note) || ' '}</span>
          </button>
          {#if index < RAIL.length - 1}
            <span class="wire" data-wire={wire(index)} aria-hidden="true"
              ><span class="fill"></span>{#if wire(index) === 'travel'}<span class="light"
                ></span>{/if}</span
            >
          {/if}
        </li>
      {/each}
    </ol>
    {#if run.replans > 0}
      <div class="arc" aria-hidden="true">
        <svg viewBox="0 0 100 22" preserveAspectRatio="none">
          <path d="M100 22 C86 1 14 1 0 22" />
          {#if pacing && run.replans > seenReplans}
            {#key run.replans}
              <path class="spark" d="M100 22 C86 1 14 1 0 22" pathLength="100" />
            {/key}
          {/if}
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
    --light-tail: var(--color-violet-400);
    --light-head: var(--color-violet-600);
    --light-glow: rgb(124 58 237 / 0.26);
  }

  :global([data-theme='dark']) .rail {
    --wire: var(--color-gray-700);
    --charged: var(--color-gray-600);
    --held: var(--color-amber-600);
    --released-ink: var(--color-white);
    --name-base: var(--color-gray-300);
    --light-tail: var(--color-violet-500);
    --light-head: var(--color-violet-200);
    --light-glow: rgb(167 139 250 / 0.36);
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

  /* The travelling light (look S3.3): a 26 px streak with a round head, gliding to 24 px short
     of the wire's end while the fill grows behind it, violet cooling to grey. */
  .light {
    position: absolute;
    inset-block-start: -1.25px;
    inset-inline-start: 0;
    inline-size: 26px;
    block-size: 1.5px;
    border-radius: 2px;
    background: linear-gradient(90deg, transparent, var(--light-tail) 55%, var(--light-head));
    box-shadow: 0 0 4px var(--light-glow);
    animation:
      travel 1900ms cubic-bezier(0.45, 0, 0.2, 1) forwards,
      fade 2450ms linear forwards;
  }

  .light::after {
    content: '';
    position: absolute;
    inset-block-start: -1.5px;
    inset-inline-end: -2px;
    inline-size: 4.5px;
    block-size: 4.5px;
    border-radius: var(--radius-pill);
    background-color: var(--light-head);
    box-shadow: 0 0 3px var(--light-glow);
  }

  .wire[data-wire='travel'] .fill {
    transform: scaleX(1);
    background-color: var(--charged);
    animation:
      grow 1900ms cubic-bezier(0.45, 0, 0.2, 1) both,
      cool 2450ms linear both;
  }

  /* The streak ends 24 px short of the wire's end: the wire is its container. */
  .wire {
    container-type: inline-size;
  }

  @keyframes travel {
    to {
      translate: calc(100cqi - 24px) 0;
    }
  }

  @keyframes fade {
    0% {
      opacity: 0;
    }
    24%,
    77.5% {
      opacity: 1;
    }
    100% {
      opacity: 0;
    }
  }

  @keyframes grow {
    from {
      transform: scaleX(0);
    }
    to {
      transform: scaleX(1);
    }
  }

  @keyframes cool {
    from {
      background-color: color-mix(in srgb, var(--light-tail) 70%, var(--charged));
    }
    70%,
    to {
      background-color: var(--charged);
    }
  }

  /* The release sweep: one violet band crosses each name in turn, once (F23). */
  .rail[data-sweep] .name {
    background: linear-gradient(
        90deg,
        currentColor 38%,
        var(--light-tail) 45%,
        var(--light-head) 50%,
        var(--light-tail) 55%,
        currentColor 62%
      )
      100% 0 / 300% 100%;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: sweep 2800ms cubic-bezier(0.37, 0, 0.63, 1) calc(1800ms + var(--index) * 220ms) both;
  }

  @keyframes sweep {
    to {
      background-position: 0 0;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .light,
    .wire[data-wire='travel'] .fill,
    .rail[data-sweep] .name {
      animation: none;
    }
  }

  .wire:is([data-wire='done'], [data-wire='released'], [data-wire='held']) .fill {
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

  /* The spark (look S3.4): a short bright dash rides the arc back once per re-plan. */
  .arc path.spark {
    stroke: var(--color-amber-500);
    stroke-width: 2.5;
    stroke-linecap: round;
    stroke-dasharray: 10 90;
    stroke-dashoffset: 10;
    animation: spark 900ms cubic-bezier(0.45, 0, 0.3, 1) 380ms both;
  }

  @keyframes spark {
    0%,
    85% {
      opacity: 1;
    }
    to {
      opacity: 0;
      stroke-dashoffset: -90;
    }
  }

  :global([data-theme='dark']) .arc path.spark {
    stroke: var(--color-yellow-300);
  }

  @media (prefers-reduced-motion: reduce) {
    .arc path.spark {
      display: none;
    }
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
