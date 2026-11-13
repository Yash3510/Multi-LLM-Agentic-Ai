<script lang="ts">
  // A checkbox with its label and an optional description. bits-ui gives the behaviour: Space
  // toggles, the mixed state (aria-checked="mixed") turns into checked on the next press, read-only
  // stops changes, and a hidden input carries the value when a name is given. Inside a Field it
  // takes its states from the Field; in a group Field the group carries the label and the error.
  import { Checkbox } from 'bits-ui';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import Icon from '../icons/Icon.svelte';
  import { getField, idList } from './field-context';
  import './choice.css';
  import './field-control.css';

  type Props = Omit<HTMLButtonAttributes, 'value' | 'children' | 'type'> & {
    checked?: boolean;
    /** Some but not all of what it stands for: a "select all" over a partly chosen list. */
    indeterminate?: boolean;
    label?: string;
    description?: string;
    /** For form submission, with value. */
    name?: string;
    value?: string;
    invalid?: boolean;
    readonly?: boolean;
    required?: boolean;
    onCheckedChange?: (checked: boolean) => void;
    /** Shows a state without interaction, for the /ui reference. */
    preview?: 'hover' | 'focus' | 'active';
    ref?: HTMLButtonElement | null;
  };

  let {
    checked = $bindable(false),
    indeterminate = $bindable(false),
    label,
    description,
    name,
    value,
    invalid,
    readonly,
    required,
    onCheckedChange,
    preview,
    ref = $bindable(null),
    id,
    disabled,
    ...rest
  }: Props = $props();

  const field = getField();
  const single = field && !field.group;
  const uid = $props.id();

  const controlId = $derived(id ?? (single ? field.id : undefined) ?? uid);
  const labelId = `${uid}-label`;
  const descriptionId = `${uid}-description`;
  const isDisabled = $derived(disabled ?? field?.disabled ?? false);
  const isReadonly = $derived(readonly ?? field?.readonly ?? false);
  const isInvalid = $derived(invalid ?? field?.invalid ?? false);
  // In a group, "required" means the group needs an answer, not that this box must be ticked.
  const isRequired = $derived(required ?? (single ? field.required : false));
</script>

<label
  class="choice"
  data-disabled={isDisabled || undefined}
  data-readonly={isReadonly || undefined}
>
  <span class="choice-slot">
    <Checkbox.Root
      bind:checked
      bind:indeterminate
      bind:ref
      id={controlId}
      {name}
      {value}
      disabled={isDisabled}
      readonly={isReadonly}
      required={isRequired}
      {onCheckedChange}
    >
      {#snippet child({ props, checked: on, indeterminate: mixed })}
        <button
          {...rest}
          {...props}
          role="checkbox"
          class="choice-mark box"
          data-invalid={isInvalid || undefined}
          data-preview={preview}
          aria-labelledby={label ? labelId : rest['aria-labelledby']}
          aria-describedby={idList(
            description && descriptionId,
            single && field.describedBy,
            rest['aria-describedby'],
          )}
          aria-invalid={isInvalid || undefined}
        >
          {#if mixed}
            <Icon name="minus" size={12} />
          {:else if on}
            <Icon name="check" size={12} />
          {/if}
        </button>
      {/snippet}
    </Checkbox.Root>
  </span>

  {#if label || description}
    <span class="choice-text">
      {#if label}<span id={labelId} class="choice-label">{label}</span>{/if}
      {#if description}<span id={descriptionId} class="choice-description">{description}</span>{/if}
    </span>
  {/if}
</label>

<style>
  /* 16 px, radius 5 px (ADR-0041 amendment). */
  .box {
    width: 16px;
    height: 16px;
    border-radius: 5px;
  }
</style>
