<script lang="ts" module>
  import type { IconName } from '$lib/ui/icons/generated/icons';

  export interface TabItem {
    value: string;
    label: string;
    icon?: IconName;
    /** A count after the label, part of the tab's name ("Open 12"). */
    count?: number;
    disabled?: boolean;
    /** Draws hover, focus or active without interaction, for /ui. */
    preview?: 'hover' | 'focus' | 'active';
  }
</script>

<script lang="ts">
  // Tabs (bits-ui). The row is one tab stop: arrow keys move between tabs, Home and End jump, and the
  // panel follows focus unless activation is manual (Enter or Space then chooses). The current tab
  // carries the selected recipe: accent-soft fill, a 2 px accent edge along its bottom and ink-1
  // text. Switching is instant: tabs are switched often and by key, so nothing slides. When the
  // tabs outgrow the row it scrolls sideways; the page never does.
  import { Tabs } from 'bits-ui';
  import type { Snippet } from 'svelte';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import { formatNumber, toIntlLocale } from '$lib/ui/format';
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    tabs: TabItem[];
    value?: string;
    /** Names the tab row. */
    label: string;
    size?: 'ui' | 'small';
    activation?: 'automatic' | 'manual';
    panel: Snippet<[TabItem]>;
    onValueChange?: (value: string) => void;
  };

  let {
    tabs,
    value = $bindable(tabs[0]?.value ?? ''),
    label,
    size = 'ui',
    activation = 'automatic',
    panel,
    onValueChange,
  }: Props = $props();

  const locale = toIntlLocale(getLocale());
</script>

<Tabs.Root bind:value {onValueChange} activationMode={activation}>
  <Tabs.List aria-label={label}>
    {#snippet child({ props })}
      <div {...props} class="list focus-inset">
        {#each tabs as tab (tab.value)}
          <Tabs.Trigger value={tab.value} disabled={tab.disabled}>
            {#snippet child({ props: tabProps })}
              <button
                {...tabProps}
                class={['tab font-medium', size === 'small' ? 'text-small' : 'text-ui']}
                data-preview={tab.preview}
              >
                {#if tab.icon}<Icon name={tab.icon} size={16} />{/if}
                <span>{tab.label}</span>
                {#if tab.count !== undefined}
                  <span class="count tabular"
                    >{formatNumber(tab.count, { decimals: 0, locale })}</span
                  >
                {/if}
              </button>
            {/snippet}
          </Tabs.Trigger>
        {/each}
      </div>
    {/snippet}
  </Tabs.List>
  {#each tabs as tab (tab.value)}
    <Tabs.Content value={tab.value}>
      {#snippet child({ props })}
        <div {...props} class="panel">{@render panel(tab)}</div>
      {/snippet}
    </Tabs.Content>
  {/each}
</Tabs.Root>

<style>
  /* The tabs sit on a line-1 rule; the current tab's edge lies along it. */
  .list {
    display: flex;
    gap: var(--spacing-1);
    overflow-x: auto;
    border-block-end: 1px solid var(--color-line-1);
    scrollbar-width: thin;
    scrollbar-color: var(--color-line-control) transparent;
  }

  .tab {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    gap: var(--spacing-1_5);
    min-block-size: var(--row-height);
    padding-inline: var(--spacing-3);
    border-start-start-radius: var(--radius-control);
    border-start-end-radius: var(--radius-control);
    color: var(--color-ink-2);
    white-space: nowrap;
    cursor: pointer;
    transition-property: background-color, color, box-shadow;
    transition-duration: var(--duration-quick);
    transition-timing-function: var(--ease-out);
  }

  .count {
    color: var(--color-ink-3);
    font-weight: var(--font-weight-normal);
  }

  @media (hover: hover) {
    .tab:not([data-disabled], [data-state='active']):hover {
      background-color: var(--color-surface-hover);
      color: var(--color-ink-1);
    }
  }

  .tab[data-preview='hover'] {
    background-color: var(--color-surface-hover);
    color: var(--color-ink-1);
  }

  .tab[data-preview='focus'] {
    outline: 2px solid var(--color-focus);
    outline-offset: -2px;
  }

  .tab:not([data-disabled]):is(:active, [data-preview='active']) {
    background-color: color-mix(in oklab, var(--color-surface-hover) 92%, var(--color-ink-1));
    color: var(--color-ink-1);
    transition-duration: var(--duration-instant);
  }

  /* Current: accent-soft fill, a 2 px accent edge along the bottom, ink-1 text. */
  .tab[data-state='active'] {
    background-color: var(--color-accent-soft);
    box-shadow: inset 0 -2px 0 var(--color-accent);
    color: var(--color-ink-1);
  }

  .tab[data-state='active'] .count {
    color: var(--color-ink-2);
  }

  .tab[data-disabled],
  .tab[data-disabled] .count {
    color: var(--color-ink-disabled);
    cursor: not-allowed;
  }

  .panel {
    padding-block-start: var(--spacing-4);
    border-radius: var(--radius-control);
  }

  @media (forced-colors: active) {
    .tab[data-state='active'] {
      border-block-end: 2px solid Highlight;
    }
  }
</style>
