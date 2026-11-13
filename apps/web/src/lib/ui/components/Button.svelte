<script lang="ts">
  // A button with a worded label, named by verb and object ("Export receipt"). Secondary by
  // default. Decision (solid ink) only for a person's decision: confirm, allow, approve, sign,
  // apply. The everyday main action is primary: raised and outlined, never filled.
  //
  // A shortcut shows as key caps after the label and is announced through aria-keyshortcuts; the
  // caller still binds the keys. Loading keeps the label and locks the width: after 300 ms the
  // six-dot ring leads the label, taking the leading icon's place, or room the button already
  // holds when it has none. The elapsed time after 10 s goes in the tooltip (ActionBase).
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { DURATION, fade } from '$lib/ui/motion.svelte';
  import ActionBase, { type ActionSize, type ActionVariant } from './ActionBase.svelte';
  import Kbd from './Kbd.svelte';
  import { ariaShortcut, isApple } from './keycap';
  import WorkingDots from './WorkingDots.svelte';

  type Props = Omit<HTMLButtonAttributes, 'disabled' | 'children'> & {
    variant?: ActionVariant;
    size?: ActionSize;
    /** Leading icon. */
    icon?: IconName;
    trailingIcon?: IconName;
    /** Keys by name, as Kbd takes them: ['mod', 'enter'] is ⌘ ↵ on Apple and Ctrl ↵ elsewhere. */
    shortcut?: string[];
    /** Pass it, even as false, on any button that can load, so its width already fits the ring. */
    loading?: boolean;
    disabled?: boolean;
    /** Why it is disabled: keeps it focusable and shows the reason in a tooltip. */
    reason?: string;
    /** Makes it a toggle: aria-pressed, and the selected look while true. */
    pressed?: boolean;
    children: Snippet;
  };

  let {
    variant = 'secondary',
    icon,
    trailingIcon,
    shortcut,
    children,
    'aria-keyshortcuts': keyshortcuts,
    ...rest
  }: Props = $props();

  const loadable = $derived(rest.loading !== undefined);
  const announced = $derived(
    keyshortcuts ?? (shortcut?.length ? ariaShortcut(shortcut, isApple()) : undefined),
  );
</script>

<ActionBase
  shape="button"
  {variant}
  data-lead={icon ? '' : undefined}
  data-trail={trailingIcon || shortcut?.length ? '' : undefined}
  aria-keyshortcuts={announced}
  {...rest}
>
  {#snippet content(clock)}
    {@const ring = clock.phase === 'ring' || clock.phase === 'timed'}
    {#if ring}
      <!-- currentColor, not violet: this is a person's action, not an agent at work. -->
      <span class="dots-slot" in:fade={{ duration: DURATION.quick }}>
        <WorkingDots size={16} />
      </span>
    {:else if icon}
      <Icon name={icon} size={16} />
    {/if}
    <span data-reserve={loadable && !icon && !ring ? '' : undefined}>{@render children()}</span>
    {#if trailingIcon}
      <Icon name={trailingIcon} size={16} />
    {/if}
    {#if shortcut?.length}
      <!-- Hidden from the name: aria-keyshortcuts says it, so it is not read twice. -->
      <Kbd keys={shortcut} aria-hidden="true" />
    {/if}
  {/snippet}
</ActionBase>

<style>
  /* WorkingDots paints with the accent role; inside an action it takes the action's own ink. */
  .dots-slot {
    --color-accent: currentColor;
    display: inline-flex;
  }
</style>
