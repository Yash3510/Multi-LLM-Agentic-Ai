<script lang="ts">
  // A single-line text field: optional leading and trailing icons, a clear button, and a copy
  // button when read-only. Its height is the row height of the density region it sits in. Inside a
  // Field it takes its id, description, error and states from the Field.
  import type { HTMLInputAttributes } from 'svelte/elements';
  import type { IconName } from '../icons/generated/icons';
  import Icon from '../icons/Icon.svelte';
  import { getField, idList, pressFocuses } from './field-context';
  import FieldButton from './FieldButton.svelte';
  import FieldCopy from './FieldCopy.svelte';
  import { fieldText } from './field-text';
  import './field-control.css';

  type Props = Omit<HTMLInputAttributes, 'value' | 'type' | 'prefix' | 'size' | 'children'> & {
    value?: string;
    type?: 'text' | 'search' | 'email' | 'url' | 'tel' | 'password';
    /** A decorative icon before the text. */
    prefix?: IconName;
    /** A decorative icon after the text. */
    suffix?: IconName;
    /** Shows a clear button while there is text to clear. */
    clearable?: boolean;
    invalid?: boolean;
    /** A sealed record (ledger, audit, released): read-only with the sealed mark in front. */
    sealed?: boolean;
    /** What the copy button copies when the shown text is shortened, e.g. the whole hash. */
    copyValue?: string;
    /** Shows a state without interaction, for the /ui reference. */
    preview?: 'hover' | 'focus';
    ref?: HTMLInputElement | null;
    clearLabel?: string;
    copyLabel?: string;
    copiedLabel?: string;
    sealedLabel?: string;
  };

  let {
    value = $bindable(''),
    type = 'text',
    prefix,
    suffix,
    clearable = false,
    invalid,
    sealed = false,
    copyValue,
    preview,
    ref = $bindable(null),
    id,
    disabled,
    readonly,
    required,
    clearLabel = fieldText.clear(),
    copyLabel = fieldText.copy(),
    copiedLabel = fieldText.copied(),
    sealedLabel = fieldText.sealed(),
    ...rest
  }: Props = $props();

  const field = getField();
  const uid = $props.id();

  const inputId = $derived(id ?? field?.id ?? uid);
  const isDisabled = $derived(disabled ?? field?.disabled ?? false);
  const isReadonly = $derived(sealed || (readonly ?? field?.readonly ?? false));
  const isInvalid = $derived(invalid ?? field?.invalid ?? false);
  const isRequired = $derived(required ?? field?.required ?? false);

  const showClear = $derived(clearable && !!value && !isDisabled && !isReadonly);
  const showCopy = $derived(isReadonly && !!value && !isDisabled);

  function clear() {
    value = '';
    ref?.focus();
  }
</script>

<div
  class="field-control"
  data-invalid={isInvalid || undefined}
  data-disabled={isDisabled || undefined}
  data-readonly={isReadonly || undefined}
  data-preview={preview}
  {@attach pressFocuses(() => ref)}
>
  {#if sealed}
    <span class="field-control-icon">
      <Icon name="lock-simple" size={16} label={sealedLabel} />
    </span>
  {:else if prefix}
    <span class="field-control-icon"><Icon name={prefix} size={16} /></span>
  {/if}

  <input
    {...rest}
    bind:this={ref}
    bind:value
    {type}
    id={inputId}
    class="field-control-input"
    disabled={isDisabled}
    readonly={isReadonly}
    aria-required={isRequired || undefined}
    aria-invalid={isInvalid || undefined}
    aria-describedby={idList(field?.describedBy, rest['aria-describedby'])}
  />

  {#if suffix}
    <span class="field-control-icon"><Icon name={suffix} size={16} /></span>
  {/if}

  {#if showClear}
    <FieldButton icon="x" label={clearLabel} onclick={clear} />
  {/if}

  {#if showCopy}
    <FieldCopy value={copyValue ?? value} label={copyLabel} {copiedLabel} />
  {/if}
</div>
