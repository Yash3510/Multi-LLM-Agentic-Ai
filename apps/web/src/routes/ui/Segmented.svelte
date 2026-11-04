<script lang="ts" generics="T extends string">
  // A labelled group of native radios drawn as one segmented pill. Native radios give arrow-key
  // movement and the radio-group semantics for free.
  type Option = { value: T; label: string; lang?: string };

  type Props = {
    label: string;
    name: string;
    options: Option[];
    value: T;
  };

  let { label, name, options, value = $bindable() }: Props = $props();

  const id = $props.id();
</script>

<div role="radiogroup" aria-labelledby="{id}-label" class="flex items-center gap-2">
  <span id="{id}-label" class="text-caption text-ink-3">{label}</span>
  <div class="track flex">
    {#each options as option (option.value)}
      <label class="segment" lang={option.lang}>
        <input class="sr-only" type="radio" {name} value={option.value} bind:group={value} />
        {option.label}
      </label>
    {/each}
  </div>
</div>

<style>
  /* The reference page's own switchers: the faint track and raised thumb the base control uses. */
  .track {
    padding: 3px;
    border-radius: 11px;
    background-color: var(--color-track);
  }

  .segment {
    display: inline-flex;
    align-items: center;
    height: 26px;
    padding-inline: 12px;
    border-radius: 8px;
    color: var(--color-ink-3);
    font-size: var(--text-small);
    line-height: var(--text-small--line-height);
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
    transition:
      background-color 150ms cubic-bezier(0.4, 0, 0.2, 1),
      box-shadow 150ms cubic-bezier(0.4, 0, 0.2, 1),
      color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .segment:hover {
    color: var(--color-ink-1);
  }

  .segment:has(:checked) {
    background-color: var(--color-surface-raised);
    box-shadow: var(--shadow-hairline);
    color: var(--color-ink-1);
    font-weight: var(--font-weight-medium);
  }

  .segment:has(:focus-visible) {
    box-shadow: var(--shadow-hairline), var(--shadow-focus);
  }
</style>
