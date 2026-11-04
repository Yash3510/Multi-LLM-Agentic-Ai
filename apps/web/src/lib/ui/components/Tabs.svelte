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
  // carries a 2 px ink edge along its bottom and ink-1 text; hover is the faint tint (ADR-0041
  // amendment). Switching is instant: tabs are switched often and by key, so nothing slides. When the
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
  /* The tabs sit on a hairline rule; the current tab carries a 2 px ink edge along it (ADR-0041
     amendment). Hover is the faint tint, focus the soft glow. */
  .list {
    display: flex;
    gap: var(--spacing-1);
    overflow-x: auto;
    box-shadow: inset 0 -1px 0 var(--color-hair);
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
    border-radius: 8px 8px 0 0;
    color: var(--color-ink-3);
    font-weight: var(--font-weight-medium);
    white-space: nowrap;
    cursor: pointer;
    transition-property: background-color, color, box-shadow;
    transition-duration: 150ms;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }

  .count {
    color: var(--color-ink-3);
    font-weight: var(--font-weight-normal);
  }

  .tab:not([data-disabled], [data-state='active']):is(
      :hover,
      :active,
      [data-preview='hover'],
      [data-preview='active']
    ) {
    background-color: var(--color-tint);
    color: var(--color-ink-1);
  }

  .tab:is(:focus-visible, [data-preview='focus']) {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .tab[data-state='active'] {
    box-shadow: inset 0 -2px 0 var(--color-ink-1);
    color: var(--color-ink-1);
  }

  .tab[data-state='active']:is(:focus-visible, [data-preview='focus']) {
    box-shadow:
      inset 0 -2px 0 var(--color-ink-1),
      var(--shadow-focus);
  }

  .tab[data-state='active'] .count {
    color: var(--color-ink-2);
  }

  .tab[data-disabled] {
    opacity: 0.45;
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
