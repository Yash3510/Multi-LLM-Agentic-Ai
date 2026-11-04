<script lang="ts">
  // A square button with only an icon, for dense toolbars; everywhere else an action has a word
  // (Button). The label is required: it is the accessible name and the hint, a tooltip that opens
  // on hover and on keyboard focus. A shortcut joins the hint as key caps. Pass a tooltip snippet
  // to say more, and keep the label in it. Quiet by default, as in toolbars. Never a decision: a
  // person's decision is always worded.
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { DURATION, fade } from '$lib/ui/motion.svelte';
  import ActionBase, { type ActionSize, type ActionVariant } from './ActionBase.svelte';
  import Kbd from './Kbd.svelte';
  import { ariaShortcut, isApple } from './keycap';
  import WorkingDots from './WorkingDots.svelte';

  type Props = Omit<HTMLButtonAttributes, 'disabled' | 'children' | 'aria-label'> & {
    icon: IconName;
    /** The accessible name and the hint. */
    label: string;
    variant?: Exclude<ActionVariant, 'decision'>;
    size?: ActionSize;
    /** Keys by name, as Kbd takes them; shown in the hint and announced with aria-keyshortcuts. */
    shortcut?: string[];
    loading?: boolean;
    disabled?: boolean;
    /** Why it is disabled: keeps it focusable and adds the reason to the hint. */
    reason?: string;
    pressed?: boolean;
    /** Replaces the label in the hint. */
    tooltip?: Snippet;
  };

  let {
    icon,
    label,
    variant = 'quiet',
    size = 'ui',
    shortcut,
    tooltip,
    'aria-keyshortcuts': keyshortcuts,
    ...rest
  }: Props = $props();

  // 18 px in the sidebar and top bar, 16 px in rows (ADR-0041 amendment).
  const iconSize = $derived(size === 'small' ? 16 : 18);
  const announced = $derived(
    keyshortcuts ?? (shortcut?.length ? ariaShortcut(shortcut, isApple()) : undefined),
  );
</script>

<ActionBase
  shape="icon"
  {variant}
  {size}
  aria-label={label}
  aria-keyshortcuts={announced}
  {...rest}
>
  {#snippet content(clock)}
    {#if clock.phase === 'ring' || clock.phase === 'timed'}
      <!-- The ring takes the icon's place, so nothing moves. -->
      <span class="dots-slot" in:fade={{ duration: DURATION.quick }}>
        <WorkingDots size={iconSize} />
      </span>
    {:else}
      <Icon name={icon} size={iconSize} />
    {/if}
  {/snippet}
  {#snippet tip()}
    <span class="flex items-center gap-2">
      {#if tooltip}{@render tooltip()}{:else}{label}{/if}
      {#if shortcut?.length}<Kbd keys={shortcut} aria-hidden="true" />{/if}
    </span>
  {/snippet}
</ActionBase>

<style>
  /* WorkingDots paints with the accent role; inside an action it takes the action's own ink. */
  .dots-slot {
    --color-accent: currentColor;
    display: inline-flex;
  }
</style>
