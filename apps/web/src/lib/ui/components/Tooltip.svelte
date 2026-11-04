<script lang="ts">
  // A hint: text only, never an action or something a person must read to go on. It opens at once
  // on keyboard focus and after 280 ms of hover intent, and waits a 160 ms grace before closing, so
  // crossing to it or slipping off for a moment does not make it flicker. Esc closes it. Never a
  // title attribute, which keyboards and touch never reach.
  //
  // The tip describes its trigger (aria-describedby), so it should add to the trigger's name rather
  // than repeat it. Give a control as the child snippet, or a short phrase as `label`: that phrase
  // becomes a focusable term with a dotted underline.
  import { Tooltip } from 'bits-ui';
  import type { Snippet } from 'svelte';
  import { graceClose, INTENT_MS } from './hover-intent';
  import Kbd from './Kbd.svelte';
  import './surfaces.css';

  type Props = {
    text: string;
    /** Keys by name, as Kbd takes them, shown after the text. */
    shortcut?: string[];
    side?: 'top' | 'bottom' | 'left' | 'right';
    /** The control the tip belongs to. Spread the props onto it. */
    children?: Snippet<[{ props: Record<string, unknown> }]>;
    /** Without children: the phrase the tip explains. */
    label?: string;
    disabled?: boolean;
    /** Opens it without interaction, for /ui. */
    open?: boolean;
  };

  let {
    text,
    shortcut,
    side = 'top',
    children,
    label,
    disabled = false,
    open = $bindable(false),
  }: Props = $props();

  const grace = graceClose((value) => (open = value));
  $effect(() => () => grace.cancel());

  // A key, a blur or a press closes at once; only a pointer leaving waits out the grace.
  const now = () => grace.immediate();
</script>

<Tooltip.Provider delayDuration={INTENT_MS}>
  <Tooltip.Root bind:open={() => open, grace.request} {disabled}>
    <Tooltip.Trigger onpointerdown={now} onblur={now} onclick={now}>
      {#snippet child({ props })}
        {#if children}
          {@render children({ props })}
        {:else}
          <button {...props} type="button" class="term">{label}</button>
        {/if}
      {/snippet}
    </Tooltip.Trigger>
    <Tooltip.Portal>
      <Tooltip.Content {side} sideOffset={6} collisionPadding={8} onEscapeKeydown={now}>
        {#snippet child({ wrapperProps, props })}
          <div {...wrapperProps}>
            <div {...props} data-surface="tip">
              <span class="flex items-center gap-2">
                {text}
                {#if shortcut?.length}<Kbd keys={shortcut} />{/if}
              </span>
            </div>
          </div>
        {/snippet}
      </Tooltip.Content>
    </Tooltip.Portal>
  </Tooltip.Root>
</Tooltip.Provider>

<style>
  /* A term with a hint: the text itself, underlined in dots, focusable like any control. */
  .term {
    display: inline;
    padding: 0;
    border-radius: var(--radius-tight);
    color: inherit;
    font: inherit;
    text-decoration-line: underline;
    text-decoration-style: dotted;
    text-decoration-color: var(--color-line-control);
    text-decoration-thickness: 1px;
    text-underline-offset: 0.25em;
    cursor: help;
    transition: text-decoration-color var(--duration-quick) var(--ease-out);
  }

  @media (hover: hover) {
    .term:hover {
      text-decoration-color: currentColor;
    }
  }
</style>
