<script lang="ts">
  // Pick one option from a short list. bits-ui gives the listbox behaviour (arrow keys, typeahead
  // on the closed trigger, Home and End, Escape, focus return); the look is the shared field box.
  // Read-only shows the chosen label as read-only text, so it can still be read and copied.
  import { Select } from 'bits-ui';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import Icon from '../icons/Icon.svelte';
  import { getField, idList } from './field-context';
  import ListboxPopup from './ListboxPopup.svelte';
  import type { FieldOption } from './options';
  import TextInput from './TextInput.svelte';
  import './field-control.css';

  type Props = Omit<HTMLButtonAttributes, 'value' | 'children'> & {
    value?: string;
    options: readonly FieldOption[];
    placeholder?: string;
    /** For form submission. */
    name?: string;
    invalid?: boolean;
    readonly?: boolean;
    required?: boolean;
    open?: boolean;
    onValueChange?: (value: string) => void;
    /** Shows a state without interaction, for the /ui reference. */
    preview?: 'hover' | 'focus' | 'active';
  };

  let {
    value = $bindable(''),
    options,
    placeholder = '',
    name,
    invalid,
    readonly,
    required,
    open = $bindable(false),
    onValueChange,
    preview,
    id,
    disabled,
    ...rest
  }: Props = $props();

  const field = getField();
  const uid = $props.id();

  const triggerId = $derived(id ?? field?.id ?? uid);
  const isDisabled = $derived(disabled ?? field?.disabled ?? false);
  const isReadonly = $derived(readonly ?? field?.readonly ?? false);
  const isInvalid = $derived(invalid ?? field?.invalid ?? false);
  const isRequired = $derived(required ?? field?.required ?? false);

  let trigger = $state<HTMLButtonElement | null>(null);

  const selected = $derived(options.find((option) => option.value === value));
  // Typeahead on the closed trigger needs the list up front, as a native select has it.
  const items = $derived(options.map(({ value, label, disabled }) => ({ value, label, disabled })));
</script>

{#if isReadonly}
  <!-- Read-only text keeps the name and still submits the value, as a read-only input would. -->
  <TextInput
    id={triggerId}
    value={selected?.label ?? ''}
    readonly
    disabled={isDisabled}
    aria-label={rest['aria-label']}
    aria-labelledby={rest['aria-labelledby']}
    aria-describedby={rest['aria-describedby']}
  />
  {#if name}<input type="hidden" {name} {value} disabled={isDisabled} />{/if}
{:else}
  <Select.Root
    type="single"
    bind:value
    bind:open
    {items}
    {name}
    disabled={isDisabled}
    required={isRequired}
    {onValueChange}
  >
    <Select.Trigger id={triggerId}>
      {#snippet child({ props })}
        <!-- Named by the field's label; a combobox reads its text, the chosen label, as its value. -->
        <button
          {...rest}
          {...props}
          bind:this={trigger}
          type="button"
          role="combobox"
          class="field-control trigger"
          data-invalid={isInvalid || undefined}
          data-disabled={isDisabled || undefined}
          data-preview={preview}
          aria-labelledby={field?.labelId ?? rest['aria-labelledby']}
          aria-describedby={idList(field?.describedBy, rest['aria-describedby'])}
          aria-invalid={isInvalid || undefined}
          aria-required={isRequired || undefined}
        >
          <span class="value" data-placeholder={selected ? undefined : ''}>
            {selected?.label ?? placeholder}
          </span>
          <span class="field-control-icon"><Icon name="caret-up-down" size={16} /></span>
        </button>
      {/snippet}
    </Select.Trigger>
    <ListboxPopup {options} anchor={trigger} />
  </Select.Root>
{/if}

<style>
  .trigger {
    cursor: pointer;
  }

  .trigger[data-disabled] {
    cursor: not-allowed;
  }

  .value {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .value[data-placeholder] {
    color: var(--color-ink-3);
  }

  .trigger[data-disabled] .value {
    color: var(--color-ink-disabled);
  }
</style>
