<script lang="ts">
  // The option list that Select and Combobox open. bits-ui's combobox reuses its select content and
  // items, so one popup serves both roots. Highlight follows the input: a pointer gets the hover
  // fill, the keyboard gets the tint with a soft blue inner edge (ADR-0041 amendment).
  import { Select } from 'bits-ui';
  import Icon from '../icons/Icon.svelte';
  import type { FieldOption } from './options';
  import WorkingDots from './WorkingDots.svelte';
  import './field-control.css';

  type Props = {
    options: readonly FieldOption[];
    /** Shown instead of the list when there is nothing to pick. */
    emptyText?: string;
    loading?: boolean;
    loadingText?: string;
    /**
     * The element to line up with and match in width. The popup also takes its language and density
     * from it, because the portal puts the list outside the region the field sits in.
     */
    anchor: HTMLElement | null;
  };

  let { options, emptyText, loading = false, loadingText, anchor }: Props = $props();

  let keyboard = $state(false);

  /** The nearest value set below <html>; the portal already inherits what <html> says. */
  function regional(name: 'lang' | 'data-density'): string | undefined {
    const region = anchor?.closest(`[${name}]`);
    return region && region !== document.documentElement
      ? (region.getAttribute(name) ?? undefined)
      : undefined;
  }
</script>

<svelte:document onkeydown={() => (keyboard = true)} onpointermove={() => (keyboard = false)} />

<Select.Portal>
  <Select.Content sideOffset={4} collisionPadding={8} customAnchor={anchor}>
    {#snippet child({ wrapperProps, props })}
      <div {...wrapperProps} lang={regional('lang')} data-density={regional('data-density')}>
        <div
          {...props}
          class="menu field-menu"
          data-keyboard={keyboard || undefined}
          aria-busy={loading}
        >
          <Select.Viewport>
            {#snippet child({ props: viewportProps })}
              <div {...viewportProps} class="viewport">
                {#if loading}
                  <!-- Spoken by the field's own status line; shown here for sight. -->
                  <p class="note" aria-hidden="true"><WorkingDots delay={300} />{loadingText}</p>
                {:else if options.length === 0}
                  <p class="note" aria-hidden="true">{emptyText}</p>
                {:else}
                  {#each options as option (option.value)}
                    <Select.Item
                      value={option.value}
                      label={option.label}
                      disabled={option.disabled}
                    >
                      {#snippet child({ props: itemProps, selected })}
                        <div {...itemProps} class="option">
                          <span class="option-label">{option.label}</span>
                          {#if selected}
                            <span class="option-check"><Icon name="check" size={16} /></span>
                          {/if}
                        </div>
                      {/snippet}
                    </Select.Item>
                  {/each}
                {/if}
              </div>
            {/snippet}
          </Select.Viewport>
        </div>
      </div>
    {/snippet}
  </Select.Content>
</Select.Portal>

<style>
  /* e2 depth, borderless like every float: a 12 px radius with 4 px inside, so the rows take 8 px
     (ADR-0041 amendment; the same rows as menu.css). */
  .menu {
    min-width: var(--bits-floating-anchor-width);
    max-width: var(--bits-floating-available-width);
    max-height: min(var(--bits-floating-available-height), calc(var(--spacing-12) * 6));
    border-radius: var(--radius-inset);
    background-color: var(--glass-fill);
    -webkit-backdrop-filter: var(--glass-blur);
    backdrop-filter: var(--glass-blur);
    box-shadow: var(--shadow-e2), var(--glass-edge);
    color: var(--color-ink-1);
    overflow: hidden;
    transition-property: opacity, transform;
    transition-duration: var(--duration-calm);
    transition-timing-function: var(--ease-out);
  }

  /* Arrives with 4 px of travel from the field it belongs to; leaves in two thirds of the time. */
  .menu[data-starting-style],
  .menu[data-ending-style] {
    opacity: 0;
    transform: translateY(calc(var(--spacing-1) * -1));
  }

  .menu[data-side='top'][data-starting-style],
  .menu[data-side='top'][data-ending-style] {
    transform: translateY(var(--spacing-1));
  }

  .menu[data-ending-style] {
    transition-duration: var(--duration-base);
    transition-timing-function: var(--ease-exit);
  }

  .viewport {
    padding: var(--spacing-1);
  }

  .option {
    position: relative;
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    min-height: var(--row-height);
    padding-inline: var(--spacing-3) var(--spacing-2);
    border-radius: 8px;
    font-size: inherit;
    line-height: var(--field-line);
    cursor: pointer;
    user-select: none;
    transition-property: background-color, color;
    transition-duration: var(--duration-quick);
    transition-timing-function: var(--ease-out);
  }

  .option-label {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .option-check {
    display: inline-flex;
    flex-shrink: 0;
  }

  .option[data-highlighted] {
    background-color: color-mix(in srgb, var(--color-gray-50) 60%, transparent);
  }

  :global([data-theme='dark']) .option[data-highlighted] {
    background-color: color-mix(in srgb, var(--color-gray-800) 60%, transparent);
  }

  /* Selected: ink-1 at medium weight with the tick, never a fill, as the menu marks its choice. */
  .option[data-selected] {
    color: var(--color-ink-1);
    font-weight: var(--font-weight-medium);
  }

  /* The keyboard's highlight: the tint plus a soft blue inner edge, not a hard ring. */
  .menu[data-keyboard] .option[data-highlighted] {
    outline: none;
    background-color: var(--color-tint);
    box-shadow: inset 0 0 0 1px var(--focus-edge);
  }

  .option[data-disabled] {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .note {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    min-height: var(--row-height);
    padding-inline: var(--spacing-3);
    color: var(--color-ink-3);
    line-height: var(--field-line);
  }

  @media (forced-colors: active) {
    .menu[data-keyboard] .option[data-highlighted] {
      outline: 2px solid Highlight;
      outline-offset: -2px;
    }
  }
</style>
