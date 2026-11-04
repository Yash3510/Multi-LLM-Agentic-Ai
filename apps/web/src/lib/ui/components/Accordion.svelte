<script lang="ts" module>
  export interface AccordionItem {
    value: string;
    label: string;
    /** Short context at the trigger's end, e.g. "3 rules". */
    detail?: string;
    disabled?: boolean;
  }
</script>

<script lang="ts">
  // A stack of disclosures (bits-ui Accordion), each trigger inside a heading. Up and Down arrows
  // move between the triggers, Home and End jump, Enter or Space toggles. `single` keeps one open at
  // a time; `multiple` lets several stay open. Each region opens by grid rows at calm, as Disclosure.
  // `value` lists the open items in either mode.
  import { Accordion } from 'bits-ui';
  import type { Snippet } from 'svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './expand.css';
  import './surfaces.css';

  type Props = {
    items: AccordionItem[];
    type?: 'single' | 'multiple';
    value?: string[];
    /** The heading level each trigger sits in. */
    level?: 2 | 3 | 4 | 5 | 6;
    disabled?: boolean;
    item: Snippet<[AccordionItem]>;
  };

  let {
    items,
    type = 'multiple',
    value = $bindable([]),
    level = 3,
    disabled = false,
    item,
  }: Props = $props();
</script>

{#snippet entries()}
  {#each items as entry (entry.value)}
    <Accordion.Item value={entry.value} disabled={entry.disabled}>
      {#snippet child({ props })}
        <div {...props} class="item">
          <Accordion.Header {level}>
            <Accordion.Trigger>
              {#snippet child({ props: triggerProps })}
                {@const open = value.includes(entry.value)}
                <button {...triggerProps} type="button" data-expand-trigger>
                  <span data-caret>
                    <Icon name={open ? 'caret-down' : 'caret-right'} size={16} />
                  </span>
                  <span data-label>{entry.label}</span>
                  {#if entry.detail}<span data-detail>{entry.detail}</span>{/if}
                </button>
              {/snippet}
            </Accordion.Trigger>
          </Accordion.Header>
          <Accordion.Content forceMount>
            {#snippet child({ props: contentProps })}
              <div {...contentProps} data-expand>
                <div>
                  <div data-expand-body>{@render item(entry)}</div>
                </div>
              </div>
            {/snippet}
          </Accordion.Content>
        </div>
      {/snippet}
    </Accordion.Item>
  {/each}
{/snippet}

{#if type === 'single'}
  <Accordion.Root
    type="single"
    {disabled}
    bind:value={() => value[0] ?? '', (next: string) => (value = next ? [next] : [])}
  >
    {#snippet child({ props })}
      <div {...props} class="accordion">{@render entries()}</div>
    {/snippet}
  </Accordion.Root>
{:else}
  <Accordion.Root type="multiple" {disabled} bind:value>
    {#snippet child({ props })}
      <div {...props} class="accordion">{@render entries()}</div>
    {/snippet}
  </Accordion.Root>
{/if}

<style>
  /* Items are separated by hairline rules, not boxed. */
  .accordion {
    display: flex;
    flex-direction: column;
  }

  .item:not(:first-child) {
    border-block-start: 1px solid var(--color-hair);
  }

  .item {
    padding-block: var(--spacing-1);
  }
</style>
