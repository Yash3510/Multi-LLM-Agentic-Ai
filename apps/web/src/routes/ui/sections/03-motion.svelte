<script module lang="ts">
  import { m } from '$lib/i18n/generated/messages.js';
  import type { SectionMeta } from '../section';

  export const section: SectionMeta = {
    id: 'motion',
    title: m.ui_section_motion,
    description: m.ui_motion_intro,
  };
</script>

<script lang="ts">
  import { untrack } from 'svelte';
  import { formatQuantity } from '$lib/ui/format';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { DURATION, EASE, motion, rise } from '$lib/ui/motion.svelte';
  import ReplayButton from '../ReplayButton.svelte';
  import { replay } from '../replay.svelte';

  type Token = keyof typeof DURATION;

  const DURATIONS: { token: Token; use: () => string }[] = [
    { token: 'instant', use: m.ui_motion_instant },
    { token: 'quick', use: m.ui_motion_quick },
    { token: 'base', use: m.ui_motion_base },
    { token: 'calm', use: m.ui_motion_calm },
    { token: 'slow', use: m.ui_motion_slow },
    { token: 'deliberate', use: m.ui_motion_deliberate },
    { token: 'handover', use: m.ui_motion_handover },
    { token: 'ambient', use: m.ui_motion_ambient },
  ];

  const EASINGS = [
    { token: 'ease-out', css: EASE.out, use: m.ui_motion_ease_out },
    { token: 'ease-in-out', css: EASE.inOut, use: m.ui_motion_ease_in_out },
    { token: 'ease-exit', css: EASE.exit, use: m.ui_motion_ease_exit },
    { token: 'linear', css: EASE.linear, use: m.ui_motion_linear },
  ];

  /** The curve of a cubic-bezier() as an SVG path in a unit box, y pointing up. */
  function curve(css: string): string {
    const [x1, y1, x2, y2] = (css.match(/[\d.]+/g) ?? []).map(Number);
    if (x1 === undefined) return 'M0 1 L1 0';
    return `M0 1 C${x1} ${1 - y1} ${x2} ${1 - y2} 1 0`;
  }

  // Each dot rests at the end of its track, so the still page shows every demo's final frame.
  const dots: Record<string, HTMLElement> = {};

  /** Runs a dot along its track. Under reduced motion nothing moves: it fades in where it rests. */
  function travel(id: string, duration: number, easing: string) {
    const dot = dots[id];
    if (!dot?.parentElement) return;
    for (const animation of dot.getAnimations()) animation.cancel();
    if (motion.reduced) {
      dot.animate([{ opacity: 0 }, { opacity: 1 }], { duration: Math.min(duration, 120) });
      return;
    }
    const distance = dot.parentElement.clientWidth - dot.offsetWidth;
    dot.animate([{ transform: `translateX(${-distance}px)` }, { transform: 'none' }], {
      duration,
      easing,
    });
  }

  // Transitions: rise in and out, a staggered list, and expand and collapse.
  let shown = $state(true);
  let open = $state(true);
  let run = $state(0);

  const CASES = ['CASE-0141', 'CASE-0142', 'CASE-0143', 'CASE-0144', 'CASE-0145', 'CASE-0146'];
  // New keys on each run, so the list's items are created again and their own intros play.
  const staggered = $derived(CASES.map((id) => ({ id, key: `${id}-${run}` })));

  const wait = (ms: number) => new Promise((done) => setTimeout(done, ms));

  /** Hides, waits for the exit to finish, and shows again. */
  async function cycle(set: (value: boolean) => void, exit: number) {
    set(false);
    await wait(motion.reduced ? 120 : exit);
    set(true);
  }

  const replayRise = () => cycle((value) => (shown = value), (DURATION.calm * 2) / 3);
  const replayExpand = () => cycle((value) => (open = value), DURATION.calm);

  function playAll() {
    for (const { token } of DURATIONS) travel(token, DURATION[token], EASE.inOut);
    for (const easing of EASINGS) travel(easing.token, DURATION.slow, easing.css);
    run += 1;
    replayRise();
    replayExpand();
  }

  $effect(() => {
    if (replay.count > 0) untrack(playAll);
  });
</script>

{#snippet track(id: string)}
  <span class="relative flex h-6 min-w-0 flex-1 items-center justify-end" aria-hidden="true">
    <span class="absolute inset-x-0 top-1/2 h-px bg-line-2"></span>
    <span bind:this={dots[id]} class="relative size-2 rounded-pill bg-ink-1"></span>
  </span>
{/snippet}

<div class="flex flex-col gap-10">
  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_motion_durations()}</h3>
    <ul class="demo-list">
      {#each DURATIONS as { token, use } (token)}
        <li class="demo-row border-t border-line-1">
          <code class="font-mono text-small text-ink-1">--duration-{token}</code>
          <span class="text-small text-ink-1 tabular">{formatQuantity(DURATION[token], 'ms')}</span>
          <span class="text-small text-ink-2">{use()}</span>
          <span class="flex items-center gap-3">
            {@render track(token)}
            <ReplayButton
              label={m.ui_replay_one({ name: token })}
              onclick={() => travel(token, DURATION[token], EASE.inOut)}
            />
          </span>
        </li>
      {/each}
    </ul>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_motion_easings()}</h3>
    <ul class="demo-list">
      {#each EASINGS as easing (easing.token)}
        <li class="demo-row border-t border-line-1">
          <span class="flex items-center gap-3">
            <svg
              viewBox="0 0 1 1"
              class="size-6 shrink-0 overflow-visible text-ink-1"
              aria-hidden="true"
            >
              <rect
                width="1"
                height="1"
                class="fill-none stroke-line-1"
                vector-effect="non-scaling-stroke"
              />
              <path
                d={curve(easing.css)}
                class="fill-none stroke-current"
                stroke-width="1.5"
                stroke-linecap="round"
                vector-effect="non-scaling-stroke"
              />
            </svg>
            <code class="font-mono text-small text-ink-1">{easing.token}</code>
          </span>
          <code class="font-mono text-caption text-ink-3">{easing.css}</code>
          <span class="text-small text-ink-2">{easing.use()}</span>
          <span class="flex items-center gap-3">
            {@render track(easing.token)}
            <ReplayButton
              label={m.ui_replay_one({ name: easing.token })}
              onclick={() => travel(easing.token, DURATION.slow, easing.css)}
            />
          </span>
        </li>
      {/each}
    </ul>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_motion_transitions()}</h3>
    <div class="grid gap-4 lg:grid-cols-3">
      <div
        class="demo flex flex-col gap-3 rounded-card border border-line-1 bg-surface-raised p-inset-card"
      >
        <div class="flex items-center justify-between gap-3">
          <p class="text-caption text-ink-2">{m.ui_motion_rise()}</p>
          <button
            type="button"
            class="quiet h-6 shrink-0 rounded-pill border border-line-1 px-3 text-small text-ink-1"
            onclick={() => (shown = !shown)}
          >
            {shown ? m.ui_motion_hide() : m.ui_motion_show()}
          </button>
        </div>
        <div class="stage flex items-center justify-center rounded-inset bg-surface-sunken">
          {#if shown}
            <div
              class="flex items-center gap-3 rounded-control border border-line-2 bg-surface-raised px-3 py-2 shadow-e1"
              in:rise
              out:rise
            >
              <code class="font-mono text-small text-ink-1">CASE-0142</code>
              <span class="text-small text-ink-2">R2</span>
            </div>
          {/if}
        </div>
      </div>

      <div
        class="demo flex flex-col gap-3 rounded-card border border-line-1 bg-surface-raised p-inset-card"
      >
        <div class="flex items-center justify-between gap-3">
          <p class="text-caption text-ink-2">{m.ui_motion_stagger()}</p>
          <ReplayButton label={m.ui_replay_one({ name: 'stagger' })} onclick={() => (run += 1)} />
        </div>
        <ol class="stage flex flex-col justify-center rounded-inset bg-surface-sunken px-3">
          {#each staggered as row, index (row.key)}
            <li class="font-mono text-caption text-ink-1" in:rise={{ delay: index * 40 }}>
              {row.id}
            </li>
          {/each}
        </ol>
      </div>

      <div
        class="demo flex flex-col gap-3 rounded-card border border-line-1 bg-surface-raised p-inset-card"
      >
        <p class="text-caption text-ink-2">{m.ui_motion_expand()}</p>
        <div class="stage flex flex-col rounded-inset bg-surface-sunken p-1">
          <button
            type="button"
            class="quiet flex h-8 items-center gap-2 rounded-control px-2 text-small text-ink-1"
            aria-expanded={open}
            aria-controls="motion-expand"
            onclick={() => (open = !open)}
          >
            <!-- The caret swaps rather than turns: no rotation in transitions. -->
            <Icon name={open ? 'caret-down' : 'caret-right'} size={16} />
            {m.ui_motion_expand_toggle()}
          </button>
          <div id="motion-expand" class="expand" class:open>
            <div class="min-h-0 overflow-hidden">
              <p class="px-2 pt-1 pb-2 text-small text-ink-2">{m.ui_motion_expand_body()}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  /* Rows share one grid (subgrid), so every column lines up down the list. */
  .demo-list {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    column-gap: var(--spacing-6);
  }

  .demo-row {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: subgrid;
    align-items: center;
    row-gap: var(--spacing-2);
    padding-block: var(--spacing-2);
  }

  .demo-row > :nth-child(3),
  .demo-row > :nth-child(4) {
    grid-column: 1 / -1;
  }

  @media (min-width: 64rem) {
    .demo-list {
      grid-template-columns: max-content max-content minmax(0, 1fr) minmax(0, 1.25fr);
    }

    .demo-row > :nth-child(3),
    .demo-row > :nth-child(4) {
      grid-column: auto;
    }
  }

  /* A fixed stage, so a card leaving or rows arriving never move the layout around them. */
  .stage {
    height: calc(var(--spacing-12) * 3);
  }

  .quiet {
    transition-property: background-color, border-color, color;
    transition-duration: var(--duration-quick);
    transition-timing-function: var(--ease-out);
  }

  .quiet:hover {
    background-color: var(--color-surface-hover);
    border-color: var(--color-line-2);
  }

  /* Expand and collapse: grid rows from 0fr to 1fr at calm. Reduced motion stops the row
     transition (app.css), so the panel opens at once. */
  .expand {
    display: grid;
    grid-template-rows: 0fr;
    transition: grid-template-rows var(--duration-calm) var(--ease-in-out);
  }

  .expand.open {
    grid-template-rows: 1fr;
  }
</style>
