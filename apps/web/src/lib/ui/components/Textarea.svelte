<script lang="ts">
  // A multi-line text field that grows with its text from `rows` to `maxRows`, then scrolls. The
  // growth is CSS only: a hidden copy of the text sits in the same grid cell and sizes the cell, so
  // it follows every change of value, font, density and script without measuring anything.
  // Read-only adds the copy button in the top corner.
  import type { HTMLTextareaAttributes } from 'svelte/elements';
  import { getField, idList } from './field-context';
  import FieldCopy from './FieldCopy.svelte';
  import { fieldText } from './field-text';
  import './field-control.css';

  type Props = Omit<HTMLTextareaAttributes, 'value' | 'rows' | 'children'> & {
    value?: string;
    /** Lines shown when empty. */
    rows?: number;
    /** Lines it grows to before it scrolls. */
    maxRows?: number;
    invalid?: boolean;
    /** Shows a state without interaction, for the /ui reference. */
    preview?: 'hover' | 'focus';
    ref?: HTMLTextAreaElement | null;
    copyLabel?: string;
    copiedLabel?: string;
  };

  let {
    value = $bindable(''),
    rows = 3,
    maxRows = 8,
    invalid,
    preview,
    ref = $bindable(null),
    id,
    disabled,
    readonly,
    required,
    copyLabel = fieldText.copy(),
    copiedLabel = fieldText.copied(),
    ...rest
  }: Props = $props();

  const field = getField();
  const uid = $props.id();

  const textareaId = $derived(id ?? field?.id ?? uid);
  const isDisabled = $derived(disabled ?? field?.disabled ?? false);
  const isReadonly = $derived(readonly ?? field?.readonly ?? false);
  const isInvalid = $derived(invalid ?? field?.invalid ?? false);
  const isRequired = $derived(required ?? field?.required ?? false);
  const showCopy = $derived(isReadonly && !!value && !isDisabled);
</script>

<div
  class="field-control multiline"
  style:--rows={rows}
  style:--max-rows={Math.max(rows, maxRows)}
  data-invalid={isInvalid || undefined}
  data-disabled={isDisabled || undefined}
  data-readonly={isReadonly || undefined}
  data-preview={preview}
>
  <!-- The trailing space keeps a final empty line counted, as the textarea shows it. -->
  <div class="grow" data-copy="{value} ">
    <textarea
      {...rest}
      bind:this={ref}
      bind:value
      id={textareaId}
      class="field-control-input"
      disabled={isDisabled}
      readonly={isReadonly}
      aria-required={isRequired || undefined}
      aria-invalid={isInvalid || undefined}
      aria-describedby={idList(field?.describedBy, rest['aria-describedby'])}></textarea>
  </div>
  {#if showCopy}
    <FieldCopy {value} label={copyLabel} {copiedLabel} />
  {/if}
</div>

<style>
  .multiline {
    align-items: stretch;
    padding: 0;
  }

  /* The copy button sits in the top corner, 4 px in, level with the first line. */
  .multiline > :global(.field-control-button) {
    align-self: flex-start;
    margin-block-start: var(--spacing-1);
    margin-inline-end: var(--spacing-1);
  }

  .multiline:has(> :global(.field-control-button)) {
    padding-inline-end: 0;
  }

  .grow {
    display: grid;
    flex: 1;
    min-width: 0;
  }

  /* The textarea and its hidden copy share one cell and every metric, so they size together. */
  .grow::after,
  .grow > textarea {
    grid-area: 1 / 1;
    /* 8 px above and below a 20 px line, 12 px at the sides, as tall as a 36 px input. */
    padding: var(--spacing-2) var(--spacing-3);
    min-height: calc(var(--rows) * 1lh + 2 * var(--spacing-2));
    max-height: calc(var(--max-rows) * 1lh + 2 * var(--spacing-2));
    overflow-wrap: anywhere;
    white-space: pre-wrap;
  }

  .grow::after {
    content: attr(data-copy);
    visibility: hidden;
    overflow: hidden;
    font: inherit;
    line-height: var(--field-line);
  }

  /* Without a width, a textarea sizes itself by its cols attribute instead of its box. */
  .grow > textarea {
    width: 100%;
    resize: none;
    overflow-y: auto;
  }
</style>
