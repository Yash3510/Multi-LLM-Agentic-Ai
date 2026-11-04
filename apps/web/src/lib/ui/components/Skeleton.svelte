<script module lang="ts">
  export type SkeletonStep =
    'micro' | 'caption' | 'small' | 'ui' | 'body' | 'title' | 'heading' | 'figure';
  export type SkeletonRadius = 'tight' | 'control' | 'inset' | 'card' | 'pill';

  // Written out in full so Tailwind finds the classes.
  const STEP: Record<SkeletonStep, string> = {
    micro: 'text-micro',
    caption: 'text-caption',
    small: 'text-small',
    ui: 'text-ui',
    body: 'text-body',
    title: 'text-title',
    heading: 'text-heading',
    figure: 'text-figure',
  };

  const RADIUS: Record<SkeletonRadius, string> = {
    tight: 'rounded-tight',
    control: 'rounded-control',
    inset: 'rounded-inset',
    card: 'rounded-card',
    pill: 'rounded-pill',
  };

  /** Each line's width in percent: full lines, then a short last one so a paragraph ends naturally. */
  export function lineWidths(lines: number, last: number): number[] {
    const count = Math.max(1, Math.floor(lines));
    const end = Math.min(100, Math.max(10, last));
    return Array.from({ length: count }, (_, index) => (index === count - 1 ? end : 100));
  }
</script>

<script lang="ts">
  // A placeholder where the layout is known, never fake agent output. Text lines take their type
  // step's real line height and a block takes a real radius, so content replaces it without moving
  // anything. Still for 300 ms, then the measured slow pulse.
  // Hidden from assistive technology: the region being loaded carries aria-busy.

  type Props = {
    /** Lines of text, each as tall as the step's line height. Ignored for a block. */
    lines?: number;
    step?: SkeletonStep;
    /** The last line's width in percent: 60 for a paragraph of several lines, 100 for one line. */
    last?: number;
    /** A block instead of text (a row, a tile, a thumbnail) with this radius. Size it with class. */
    block?: SkeletonRadius;
    class?: string;
  };

  let { lines = 1, step = 'ui', last, block, class: className = '' }: Props = $props();

  const widths = $derived(lineWidths(lines, last ?? (lines > 1 ? 60 : 100)));
</script>

{#if block}
  <span class="bone block max-w-full {RADIUS[block]} {className}" aria-hidden="true"></span>
{:else}
  <span class="flex flex-col {STEP[step]} {className}" aria-hidden="true">
    {#each widths as width, index (index)}
      <span class="line flex max-w-full items-center" style="width: {width}%">
        <span class="bone bar w-full rounded-tight"></span>
      </span>
    {/each}
  </span>
{/if}

<style>
  /* The measured reading bars (chat-composer look §4.5): grey 100 (grey 800 in dark), pulsing to
     half opacity every 1.2 s. Reduced motion stops the loop on full opacity. */
  .bone {
    background-color: var(--color-gray-100);
    animation: bone 1.2s ease-in-out 300ms infinite;
  }

  :global([data-theme='dark']) .bone {
    background-color: var(--color-gray-800);
  }

  /* A line box as tall as real text; the bar covers the glyphs' height (0.75 em) in its middle. */
  .line {
    height: 1lh;
  }

  .bar {
    height: 0.75em;
  }

  @keyframes bone {
    50% {
      opacity: 0.5;
    }
  }
</style>
