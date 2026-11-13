<script lang="ts">
  // An action that reads as text, for secondary actions beside content ("Show all", "Clear").
  // It is a button: for going somewhere, use Link.
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ActionBase, { type ActionSize } from './ActionBase.svelte';

  type Props = Omit<HTMLButtonAttributes, 'disabled' | 'children'> & {
    size?: ActionSize;
    icon?: IconName;
    trailingIcon?: IconName;
    disabled?: boolean;
    /** Why it is disabled: keeps it focusable and shows the reason in a tooltip. */
    reason?: string;
    children: Snippet;
  };

  let { icon, trailingIcon, children, ...rest }: Props = $props();
</script>

<ActionBase shape="text" {...rest}>
  {#snippet content()}
    {#if icon}<Icon name={icon} size={16} />{/if}
    <span>{@render children()}</span>
    {#if trailingIcon}<Icon name={trailingIcon} size={16} />{/if}
  {/snippet}
</ActionBase>
