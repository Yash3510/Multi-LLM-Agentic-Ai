<script lang="ts">
  // The live status line and run history (own-4ce look S5, features F26), directly under the
  // rail. While the run is live it says what is happening now, rolling through the stage's lines
  // every 3.8 s; afterwards it becomes a quiet summary that opens the full history.
  import type { Role, StreamEvent } from '$lib/data';
  import { deriveRun, formatStageTime, type RailStage } from '$lib/data/stages';
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    events: StreamEvent[];
    finished: boolean;
    /** The rail's light is travelling to this role: the line says so until it lands. */
    handover?: RailStage;
  };

  let { events, finished, handover }: Props = $props();

  const PASSING: Record<RailStage, string> = {
    planner: 'Passing to Planner…',
    analyst: 'Passing to Analyst…',
    author: 'Passing to Author…',
    challenger: 'Passing to Challenger…',
    'sign-off': 'Passing to you for sign-off…',
  };

  // What each role says while it works (look S5). Reader has no pool: its own words show.
  const VOICES: Partial<Record<Role | 'replan', string[]>> = {
    planner: [
      'Reading your request…',
      'Working out what kind of job this is…',
      'Picking the right model for it…',
      'Lining up the crew…',
    ],
    analyst: [
      "Working out what's actually being asked…",
      'Separating fact from assumption…',
      'Working only from what it has been given…',
      'Labelling every assumption…',
      'Checking whether the evidence is enough…',
      'Weighing the details…',
    ],
    author: [
      'Drafting the deliverable…',
      "Turning the Analyst's analysis into an answer…",
      'Giving it a proper structure…',
      'Choosing the right words…',
      'Putting it all together…',
    ],
    challenger: [
      'Looking for unsupported statements…',
      'Checking for missing steps…',
      'Hunting for arithmetic slips…',
      'Watching for made-up detail…',
      'Trying to break it…',
      "Playing devil's advocate…",
    ],
    replan: [
      "Taking the Challenger's objections on board…",
      'Sending it back through the chain…',
      'Rethinking the approach…',
    ],
    'sign-off': [
      'Waiting for your sign-off…',
      'Nothing is released until you approve it…',
      'Review the draft below…',
    ],
  };

  const statuses = $derived(events.filter((event) => event.type === 'status'));
  const latest = $derived(statuses.at(-1));
  const stopped = $derived(
    events.some((event) => event.type === 'stopped' || event.type === 'error'),
  );
  const run = $derived(deriveRun(events, finished, Date.now()));

  /** "Planner: reading the request" reads "Reading the request": the rail already says who. */
  const plain = (description: string) => {
    const text = description.replace(/^[A-Za-z-]+:\s*/, '');
    return text.charAt(0).toUpperCase() + text.slice(1);
  };

  let rolled = $state<string | undefined>();
  let open = $state(false);

  // While a stage stays open, roll to another of its lines every 3.8 s, never the same twice.
  $effect(() => {
    rolled = undefined;
    const pool = latest && !finished ? VOICES[latest.stage] : undefined;
    if (!pool) return;
    const timer = setInterval(() => {
      const others = pool.filter((line) => line !== rolled);
      rolled = others[Math.floor(Math.random() * others.length)];
    }, 3800);
    return () => clearInterval(timer);
  });

  const steps = (count: number) => `${count} ${count === 1 ? 'step' : 'steps'}`;
  const summary = $derived(
    stopped
      ? `Stopped after ${steps(statuses.length)}`
      : `${steps(statuses.length)}${run.workingMs > 0 ? ` in ${formatStageTime(run.workingMs)}` : ''}`,
  );
</script>

{#if latest}
  <div class="status-line" data-live={finished ? undefined : ''}>
    <button
      type="button"
      class="toggle"
      aria-label="Toggle status history"
      aria-expanded={open}
      onclick={() => (open = !open)}
    >
      {#if finished}
        <span class="summary">{summary}</span>
        <span class="caret" data-open={open ? '' : undefined}
          ><Icon name="caret-right" size={12} /></span
        >
      {:else}
        {@const line = handover ? PASSING[handover] : (rolled ?? plain(latest.description))}
        {#key line}
          <span class="live">{line}</span>
        {/key}
      {/if}
    </button>
    <span class="sr-only" aria-live="polite">{plain(latest.description)}</span>
    {#if open && statuses.length > 1}
      <ol class="history">
        {#each statuses as item, index (index)}
          <li class="item" data-last={index === statuses.length - 1 ? '' : undefined}>
            <span class="gutter" aria-hidden="true"><span class="dot"></span></span>
            <span class="item-text">{item.description}</span>
          </li>
        {/each}
      </ol>
    {/if}
  </div>
{/if}

<style>
  .status-line {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    margin-block-end: var(--spacing-2);
    font-size: 13.5px;
    transition:
      font-size 300ms,
      margin 300ms;
  }

  .status-line[data-live] {
    margin-block-end: 0;
    font-size: var(--text-body);
  }

  .toggle {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    max-inline-size: 100%;
    padding-block: 2px;
    color: var(--color-gray-600);
    text-align: start;
    transition: color 200ms;
  }

  :global([data-theme='dark']) .toggle {
    color: var(--color-gray-400);
  }

  .status-line:not([data-live]) .toggle:hover {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .status-line:not([data-live]) .toggle:hover {
    color: var(--color-white);
  }

  .toggle:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .summary,
  .live {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* While live, a violet light glides across the letters, then rests (look S5). */
  .live {
    background: linear-gradient(
        90deg,
        var(--color-gray-600) 38%,
        var(--color-violet-400) 45%,
        var(--color-violet-600) 50%,
        var(--color-violet-400) 55%,
        var(--color-gray-600) 62%
      )
      100% 0 / 300% 100%;
    background-clip: text;
    color: transparent;
    animation:
      glide 3.8s cubic-bezier(0.37, 0, 0.63, 1) 400ms infinite,
      rise 340ms ease-out;
  }

  :global([data-theme='dark']) .live {
    background-image: linear-gradient(
      90deg,
      var(--color-gray-400) 38%,
      var(--color-violet-500) 45%,
      var(--color-violet-200) 50%,
      var(--color-violet-500) 55%,
      var(--color-gray-400) 62%
    );
  }

  .caret {
    display: inline-flex;
    transition: rotate 300ms ease-out;
  }

  .caret[data-open] {
    rotate: 90deg;
  }

  .history {
    margin-block-start: var(--spacing-1);
  }

  .item {
    display: flex;
    gap: 10px;
    margin-block-end: var(--spacing-1);
  }

  .gutter {
    position: relative;
    display: flex;
    flex-shrink: 0;
    justify-content: center;
    inline-size: 14px;
    padding-block: 12px 6px;
  }

  .dot {
    inline-size: 6px;
    block-size: 6px;
    border-radius: var(--radius-pill);
    background-color: color-mix(in srgb, var(--color-gray-400) 70%, transparent);
  }

  .item:not([data-last]) .gutter::after {
    content: '';
    position: absolute;
    inset-block: 24px -4px;
    inline-size: 1px;
    background: linear-gradient(
      color-mix(in srgb, var(--color-gray-300) 80%, transparent),
      color-mix(in srgb, var(--color-gray-200) 40%, transparent)
    );
  }

  .item-text {
    overflow: hidden;
    padding-block: 2px;
    color: var(--color-gray-500);
    font-size: var(--text-body);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  @keyframes glide {
    0% {
      background-position: 100% 0;
    }
    63%,
    100% {
      background-position: 0 0;
    }
  }

  @keyframes rise {
    from {
      opacity: 0;
      translate: 0 10px;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .live {
      animation: none;
      background: none;
      color: var(--color-gray-600);
    }
  }
</style>
