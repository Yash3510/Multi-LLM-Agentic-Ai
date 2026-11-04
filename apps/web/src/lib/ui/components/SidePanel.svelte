<script lang="ts">
  // The shared dock where everyday tasks open: details, edits, exhibits. Not modal: no scrim, no
  // focus trap, the page beside it stays usable. On a desktop it docks in the flow at the end of the
  // row that holds it, so the page reflows beside it; on a tablet it is a full-height layer on the
  // right edge. Place it as the last child of a flex row.
  //
  // Focus: opening moves focus to the panel's title, so a screen reader announces it and Tab goes on
  // into the task. Esc closes it while focus is inside; closing hands focus back to whatever opened
  // it, but only when focus was in the panel, never pulling it away from the page.
  import { tick, untrack, type Snippet } from 'svelte';
  import { DURATION, fade } from '$lib/ui/motion.svelte';
  import IconButton from './IconButton.svelte';
  import Panel from './Panel.svelte';
  import './surfaces.css';

  type Props = {
    open?: boolean;
    title: string;
    description?: string;
    /** The close button's name and hint. */
    closeLabel: string;
    size?: 'default' | 'wide';
    /** A row under the title: tabs or a search field. */
    toolbar?: Snippet;
    children: Snippet;
    /** The actions row: primary first, named by verb and object. */
    actions?: Snippet<[{ close: () => void }]>;
    onOpenChange?: (open: boolean) => void;
    /** Where focus returns on close. By default, the element that had focus when it opened. */
    returnFocus?: HTMLElement | null;
  };

  let {
    open = $bindable(false),
    title,
    description,
    closeLabel,
    size = 'default',
    toolbar,
    children,
    actions,
    onOpenChange,
    returnFocus,
  }: Props = $props();

  let panel = $state<HTMLElement>();
  let heading = $state<HTMLElement>();
  let opener: HTMLElement | null = null;
  let wasOpen = false;

  function close() {
    open = false;
    onOpenChange?.(false);
  }

  $effect(() => {
    const now = open;
    untrack(() => {
      if (now && !wasOpen) {
        const active = document.activeElement;
        opener = returnFocus ?? (active instanceof HTMLElement ? active : null);
        tick().then(() => heading?.focus());
      } else if (!now && wasOpen) {
        const active = document.activeElement;
        const focusWasInside = !!panel && (panel.contains(active) || active === document.body);
        if (focusWasInside && opener?.isConnected) opener.focus();
        opener = null;
      }
    });
    wasOpen = now;
  });

  function keydown(event: KeyboardEvent) {
    if (event.key !== 'Escape' || event.isComposing || event.defaultPrevented) return;
    // A control inside whose own popup is open (a menu, a list) closes that first.
    const target = event.target as HTMLElement | null;
    if (target?.closest('[aria-expanded="true"]')) return;
    event.preventDefault();
    close();
  }
</script>

{#snippet closeButton()}
  <IconButton icon="x" label={closeLabel} shortcut={['esc']} onclick={close} />
{/snippet}

{#snippet panelActions()}
  {@render actions?.({ close })}
{/snippet}

{#if open}
  <div class="dock" data-placement="dock" data-size={size} out:fade={{ duration: DURATION.slow }}>
    <Panel
      bind:ref={panel}
      bind:heading
      element="aside"
      class="dock-panel"
      {title}
      {description}
      {toolbar}
      headerEnd={closeButton}
      actions={actions ? panelActions : undefined}
      onkeydown={keydown}
    >
      {@render children()}
    </Panel>
  </div>
{/if}

<style>
  .dock {
    display: flex;
  }

  .dock :global(.dock-panel) {
    flex: 1 1 auto;
    min-inline-size: 0;
  }

  /* On a tablet it meets the right edge, so only its leading corners are rounded. */
  @media (max-width: 63.98rem) {
    .dock :global(.dock-panel) {
      border-start-end-radius: 0;
      border-end-end-radius: 0;
    }
  }
</style>
