<script lang="ts">
  // The option list that Select and Combobox open. bits-ui's combobox reuses its select content and
  // items, so one popup serves both roots. Highlight follows the input: a pointer gets the hover
  // surface, the keyboard gets the focus outline (inset, as everywhere inside a scroll area).
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
  /* e2 depth: a popover. Radius card; 8 px inside, so the rows take the control radius. */
  .menu {
    min-width: var(--bits-floating-anchor-width);
    max-width: var(--bits-floating-available-width);
    max-height: min(var(--bits-floating-available-height), calc(var(--spacing-12) * 6));
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-card);
    background-color: var(--color-surface-raised);
    box-shadow: var(--shadow-e2);
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
    padding: var(--spacing-2);
  }

  .option {
    position: relative;
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    min-height: var(--row-height);
    padding-inline: var(--spacing-3) var(--spacing-2);
    border-radius: var(--radius-control);
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
    background-color: var(--color-surface-hover);
  }

  /* Selected: accent-soft fill, a 2 px accent edge and ink-1 text, plus the tick for non-colour. */
  .option[data-selected] {
    background-color: var(--color-accent-soft);
    color: var(--color-ink-1);
  }

  /* The edge is a bar, not a border, so it stays straight inside the rounded shape. */
  .option[data-selected]::before {
    content: '';
    position: absolute;
    inset-block: var(--spacing-1_5);
    inset-inline-start: 0;
    width: 2px;
    border-radius: var(--radius-pill);
    background-color: var(--color-accent);
  }

  /* Keyboard highlight is focus: the outline, turned inward inside the scroll area. */
  .menu[data-keyboard] .option[data-highlighted] {
    outline: 2px solid var(--color-focus);
    outline-offset: -2px;
  }

  .option[data-disabled] {
    color: var(--color-ink-disabled);
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
</style>
