<script lang="ts">
  // The loading state where a spinner used to be: a short length of the stage rail's wire with a
  // light travelling it (ADR-0042). It takes the text colour, so it sits in any button. Reduced
  // motion stops the loop, and the resting style, a lit wire, is its still frame.

  type Props = {
    /** In CSS pixels; 16 beside a label. */
    width?: number;
    /** Names it for assistive technology. Leave it out when visible text already says what is loading. */
    label?: string;
  };

  let { width = 16, label }: Props = $props();
</script>

<span
  class="wire"
  style:inline-size="{width}px"
  role={label ? 'img' : undefined}
  aria-label={label}
  aria-hidden={label ? undefined : true}><span class="light"></span></span
>

<style>
  .wire {
    position: relative;
    display: inline-block;
    flex-shrink: 0;
    block-size: 2px;
    overflow: hidden;
    border-radius: 1px;
    background-color: color-mix(in srgb, currentcolor 25%, transparent);
  }

  .light {
    position: absolute;
    inset-block: 0;
    inset-inline-start: 0;
    inline-size: 60%;
    border-radius: inherit;
    background: linear-gradient(90deg, transparent, currentcolor);
    animation: wire-travel var(--duration-deliberate) var(--ease-in-out) infinite;
  }

  @keyframes wire-travel {
    from {
      translate: -100% 0;
    }

    to {
      translate: 167% 0;
    }
  }
</style>
