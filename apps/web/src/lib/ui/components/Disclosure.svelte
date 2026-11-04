<script lang="ts">
  // Shows and hides one region under a worded trigger (bits-ui Collapsible): Enter or Space toggles,
  // aria-expanded says which. The region opens by grid rows from 0fr to 1fr at calm and closes in
  // two thirds of that, so nothing jumps in height; while closed it is out of the tab order.
  import { Collapsible } from 'bits-ui';
  import type { Snippet } from 'svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './expand.css';
  import './surfaces.css';

  type Props = {
    label: string;
    /** Short context at the trigger's end, e.g. "3 rules". */
    detail?: string;
    open?: boolean;
    disabled?: boolean;
    /** Draws hover, focus or active without interaction, for /ui. */
    preview?: 'hover' | 'focus' | 'active';
    children: Snippet;
  };

  let {
    label,
    detail,
    open = $bindable(false),
    disabled = false,
    preview,
    children,
  }: Props = $props();
</script>

<Collapsible.Root bind:open {disabled}>
  <Collapsible.Trigger>
    {#snippet child({ props })}
      <button {...props} type="button" data-expand-trigger data-preview={preview}>
        <span data-caret><Icon name={open ? 'caret-down' : 'caret-right'} size={16} /></span>
        <span data-label>{label}</span>
        {#if detail}<span data-detail>{detail}</span>{/if}
      </button>
    {/snippet}
  </Collapsible.Trigger>
  <Collapsible.Content forceMount>
    {#snippet child({ props })}
      <div {...props} data-expand>
        <div>
          <div data-expand-body>{@render children()}</div>
        </div>
      </div>
    {/snippet}
  </Collapsible.Content>
</Collapsible.Root>
