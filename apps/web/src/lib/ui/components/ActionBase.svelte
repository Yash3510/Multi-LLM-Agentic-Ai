<script lang="ts" module>
  /**
   * decision: solid ink, only for a person's decision (confirm, allow, approve, sign, apply).
   * primary: the everyday main action, raised and outlined. secondary: the default. quiet: low
   * emphasis, toolbars. danger: destructive.
   */
  export type ActionVariant = 'decision' | 'primary' | 'secondary' | 'quiet' | 'danger';
  /** The two type steps a control can sit on: ui (14 px) or small (13 px). */
  export type ActionSize = 'ui' | 'small';
</script>

<script lang="ts">
  // What Button, IconButton and TextButton share: the native button, the disabled and loading
  // rules, and the tooltip. The look is in actions.css.
  //
  // - Disabled with a reason stays focusable (aria-disabled), and its tooltip, a focusable popover
  //   from bits-ui rather than a title attribute, says why; a press or a tap shows it too. Without
  //   a reason it is natively disabled and leaves the tab order.
  // - Loading keeps focus, ignores presses and sets aria-busy. The elapsed time after 10 s goes in
  //   the tooltip, never in the button, so the width stays locked. The tooltip opens by itself only
  //   on the control the person pressed: a page of loading rows does not sprout a dozen tips.
  import { Tooltip } from 'bits-ui';
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import { formatDuration, toIntlLocale } from '$lib/ui/format';
  import { DURATION } from '$lib/ui/motion.svelte';
  import { loadingClock, type LoadingClock } from './action-loading.svelte';
  import './actions.css';

  type Props = Omit<HTMLButtonAttributes, 'disabled' | 'children'> & {
    shape: 'button' | 'icon' | 'text';
    variant?: ActionVariant;
    size?: ActionSize;
    /** Pass it, even as false, on anything that can load. */
    loading?: boolean;
    disabled?: boolean;
    /** Why it is disabled. Keeps the control focusable and puts the reason in its tooltip. */
    reason?: string;
    /** Makes it a toggle (aria-pressed) and draws the selected state while true. */
    pressed?: boolean;
    /** Tooltip content shown above the reason. It repeats the name, so it is not also a description. */
    tip?: Snippet;
    content: Snippet<[LoadingClock]>;
  };

  let {
    shape,
    variant,
    size = 'ui',
    loading,
    disabled = false,
    reason,
    pressed,
    type = 'button',
    onclick,
    tip,
    content,
    'aria-describedby': describedBy,
    ...rest
  }: Props = $props();

  const id = $props.id();
  const clock = loadingClock(() => !!loading && !disabled);
  const explained = $derived(disabled && !!reason);
  const timed = $derived(clock.phase === 'timed');
  // From which props are passed, not their values, so a state change never adds or removes the
  // tooltip around the button, which would remount it and drop its focus.
  const tipped = $derived(!!tip || reason !== undefined || loading !== undefined);

  let open = $state(false);
  /** The person pressed this control and it is still loading because of it. */
  let pressedHere = $state(false);
  let wasLoading = false;

  $effect(() => {
    const now = !!loading;
    if (wasLoading && !now) pressedHere = false;
    wasLoading = now;
  });

  // The elapsed-time tip opens by itself, so closing it (Escape, or the pointer leaving) must stick.
  function setOpen(value: boolean) {
    open = value;
    if (!value && timed) pressedHere = false;
  }

  function click(event: MouseEvent & { currentTarget: EventTarget & HTMLButtonElement }) {
    if (disabled || loading) {
      // Also stops a submit button from sending its form.
      event.preventDefault();
      if (explained) open = true;
      return;
    }
    pressedHere = loading !== undefined;
    onclick?.(event);
  }

  const attrs: HTMLButtonAttributes = $derived({
    ...rest,
    type,
    disabled: disabled && !reason,
    'aria-disabled': explained ? 'true' : undefined,
    'aria-busy': loading && !disabled ? 'true' : undefined,
    'aria-pressed': pressed,
    'data-action': shape,
    'data-variant': variant,
    'data-size': size,
    onclick: click,
  });
</script>

{#snippet button(props: HTMLButtonAttributes)}
  <!-- The tooltip would describe the button with its own text, so the description is set here. -->
  <button
    {...props}
    class={[props.class, size === 'small' ? 'text-small' : 'text-ui', 'font-medium']}
    aria-describedby={explained ? `${id}-reason` : describedBy}
  >
    {@render content(clock)}
    {#if explained}
      <span id="{id}-reason" hidden>{reason}</span>
    {/if}
  </button>
{/snippet}

{#if tipped}
  <Tooltip.Provider delayDuration={DURATION.slow} disableCloseOnTriggerClick={explained}>
    <!-- Nothing to say (no tip, not explained, not yet timed): it never opens. -->
    <Tooltip.Root
      bind:open={() => open || (timed && pressedHere), setOpen}
      disabled={!tip && !explained && !timed}
    >
      <Tooltip.Trigger {...attrs as Tooltip.TriggerProps}>
        {#snippet child({ props })}
          {@render button(props as HTMLButtonAttributes)}
        {/snippet}
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          data-action-tip=""
          sideOffset={6}
          collisionPadding={8}
          class="flex flex-col gap-0.5 rounded-control border border-line-1 bg-surface-raised px-2 py-1 text-caption text-ink-1 shadow-e2"
        >
          {@render tip?.()}
          {#if explained}
            <span class={tip ? 'text-ink-2' : undefined}>{reason}</span>
          {/if}
          {#if timed}
            <span class={[tip && 'text-ink-2', 'tabular']}>
              {formatDuration(clock.seconds, { locale: toIntlLocale(getLocale()) })}
            </span>
          {/if}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  </Tooltip.Provider>
{:else}
  {@render button(attrs)}
{/if}

<style>
  /* Opacity only, at base; leaving takes two thirds of that. Reduced motion caps both at 120 ms. */
  :global([data-action-tip]) {
    max-inline-size: calc(var(--spacing-12) * 6);
    transition: opacity var(--duration-base) var(--ease-out);
  }

  :global([data-action-tip][data-starting-style]) {
    opacity: 0;
  }

  :global([data-action-tip][data-ending-style]) {
    opacity: 0;
    transition-duration: calc(var(--duration-base) * 2 / 3);
    transition-timing-function: var(--ease-exit);
  }
</style>
