<script lang="ts">
  // The settings select (common look F18): the browser's own list behind a 28 px field that
  // fits its text, with a bold chevron 8 px from the end.
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    label: string;
    value: string;
    options: { value: string; label: string }[];
    onchange: (value: string) => void;
    /** Fill the row instead of fitting the text. */
    wide?: boolean;
  };

  let { label, value, options, onchange, wide = false }: Props = $props();
</script>

<span class="wrap" class:wide>
  <select aria-label={label} {value} onchange={(event) => onchange(event.currentTarget.value)}>
    {#each options as option (option.value)}
      <option value={option.value}>{option.label}</option>
    {/each}
  </select>
  <span class="chevron" aria-hidden="true"><Icon name="caret-down-bold" size={14} /></span>
</span>

<style>
  .wrap {
    position: relative;
    display: inline-flex;
    max-inline-size: 100%;
  }

  .wide,
  .wide select {
    inline-size: 100%;
  }

  select {
    max-inline-size: 100%;
    block-size: 30px;
    padding-inline: 14px 32px;
    overflow: hidden;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: var(--radius-pill);
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    line-height: 16px;
    text-overflow: ellipsis;
    appearance: none;
    field-sizing: content;
    transition: border-color 150ms;
  }

  select:focus {
    border-color: var(--color-blue-400);
    outline: none;
  }

  :global([data-theme='dark']) select {
    border-color: rgb(255 255 255 / 0.04);
    background-color: rgb(255 255 255 / 0.03);
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) select:focus {
    border-color: var(--color-blue-500);
  }

  .chevron {
    position: absolute;
    inset-block: 0;
    inset-inline-end: 8px;
    display: flex;
    align-items: center;
    color: var(--color-gray-400);
    pointer-events: none;
  }

  :global([data-theme='dark']) .chevron {
    color: var(--color-gray-500);
  }
</style>
