<script module lang="ts">
  // Six dots on the corners of a pointy-top hexagon (the logo's true 30° construction), clockwise
  // from the top, on a 14-unit box: ring radius 5, dot radius 1.5, so neighbours sit 2 units apart.
  export const DOTS = [-90, -30, 30, 90, 150, 210].map((degrees) => {
    const angle = (degrees * Math.PI) / 180;
    return [7 + 5 * Math.cos(angle), 7 + 5 * Math.sin(angle)].map((v) => Math.round(v * 1e3) / 1e3);
  });
</script>

<script lang="ts">
  // The working state: six violet dots, one light walking round them once per ambient beat. It
  // replaces every spinner. The resting style is the still frame (six full dots), so reduced motion,
  // which stops every loop, shows exactly that.

  type Props = {
    /** In CSS pixels; 14 beside text. */
    size?: number;
    /** Names it for assistive technology. Leave it out when visible text already says what is working. */
    label?: string;
    /** Milliseconds before it shows. Loading states pass 300, so quick answers never flash a ring. */
    delay?: number;
  };

  let { size = 14, label, delay = 0 }: Props = $props();

  let waited = $state(false);
  const shown = $derived(delay <= 0 || waited);

  $effect(() => {
    if (delay <= 0) return;
    const timer = setTimeout(() => (waited = true), delay);
    return () => clearTimeout(timer);
  });
</script>

<!-- Hidden, not absent, while it waits: the space is kept so the label beside it never shifts. -->
<svg
  class="dots text-accent"
  class:waiting={!shown}
  viewBox="0 0 14 14"
  width={size}
  height={size}
  fill="currentColor"
  role={label ? 'img' : undefined}
  aria-label={label}
  aria-hidden={label ? undefined : true}
>
  {#each DOTS as [cx, cy], index (index)}
    <circle {cx} {cy} r="1.5" style="--dot: {index}" />
  {/each}
</svg>

<style>
  .dots {
    flex-shrink: 0;
  }

  .waiting {
    visibility: hidden;
  }

  /*
   * Opacity only, linear because it is a loop. Each dot runs the same breathe, offset by a sixth of
   * the beat, so the brightest dot steps clockwise: dot n peaks n sixths into the beat.
   */
  circle {
    animation: breathe var(--duration-ambient) linear infinite;
    animation-delay: calc(var(--duration-ambient) * (var(--dot) / 6 - 1));
  }

  .waiting circle {
    animation-play-state: paused;
  }

  @keyframes breathe {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.25;
    }
  }
</style>
