<script lang="ts">
  // Pick one option from a longer list by typing to narrow it. bits-ui gives the combobox behaviour
  // (arrow keys from the input, Enter to pick, Escape, aria-activedescendant, focus staying in the
  // input); the filter is ours (options.ts), so matches are ranked and Devanagari signs stay whole.
  // The text always returns to the chosen label when the list closes, so it never shows a guess.
  import { Combobox } from 'bits-ui';
  import type { HTMLInputAttributes } from 'svelte/elements';
  import type { IconName } from '../icons/generated/icons';
  import Icon from '../icons/Icon.svelte';
  import { getField, idList, pressFocuses } from './field-context';
  import FieldButton from './FieldButton.svelte';
  import { fieldText } from './field-text';
  import ListboxPopup from './ListboxPopup.svelte';
  import { filterOptions, type FieldOption } from './options';
  import TextInput from './TextInput.svelte';
  import './field-control.css';

  type Props = Omit<
    HTMLInputAttributes,
    'value' | 'type' | 'prefix' | 'size' | 'children' | 'oninput'
  > & {
    value?: string;
    options: readonly FieldOption[];
    /** For form submission. */
    name?: string;
    /** A decorative icon before the text. */
    prefix?: IconName;
    invalid?: boolean;
    open?: boolean;
    /** Options are still arriving: the list says so instead of "No matches". */
    loading?: boolean;
    onValueChange?: (value: string) => void;
    /** Shows a state without interaction, for the /ui reference. */
    preview?: 'hover' | 'focus';
    clearLabel?: string;
    showOptionsLabel?: string;
    noMatchesText?: string;
    loadingText?: string;
  };

  let {
    value = $bindable(''),
    options,
    name,
    prefix,
    invalid,
    open = $bindable(false),
    loading = false,
    onValueChange,
    preview,
    id,
    disabled,
    readonly,
    required,
    clearLabel = fieldText.clear(),
    showOptionsLabel = fieldText.showOptions(),
    noMatchesText = fieldText.noMatches(),
    loadingText = fieldText.loading(),
    ...rest
  }: Props = $props();

  const field = getField();
  const uid = $props.id();

  const inputId = $derived(id ?? field?.id ?? uid);
  const isDisabled = $derived(disabled ?? field?.disabled ?? false);
  const isReadonly = $derived(readonly ?? field?.readonly ?? false);
  const isInvalid = $derived(invalid ?? field?.invalid ?? false);
  const isRequired = $derived(required ?? field?.required ?? false);

  const selected = $derived(options.find((option) => option.value === value));
  const items = $derived(options.map(({ value, label, disabled }) => ({ value, label, disabled })));

  let input = $state<HTMLInputElement | null>(null);
  let box = $state<HTMLElement | null>(null);
  // What the input shows. Typing sets it and starts filtering; closing puts the chosen label back.
  let text = $state('');
  let filtering = $state(false);

  $effect(() => {
    if (open) return;
    text = selected?.label ?? '';
    filtering = false;
  });

  // Opening from the button or arrow keys shows every option, not just those matching the label.
  const shown = $derived(filtering ? filterOptions(options, text) : [...options]);
  const showClear = $derived(!!(value || text) && !isDisabled);

  // Said once per change while the list is open, so typing reports how much is left.
  const status = $derived.by(() => {
    if (!open) return '';
    if (loading) return loadingText;
    if (!filtering) return '';
    return shown.length ? fieldText.matches(shown.length) : noMatchesText;
  });

  function type(event: Event & { currentTarget: HTMLInputElement }) {
    text = event.currentTarget.value;
    filtering = true;
  }

  function choose(next: string) {
    filtering = false;
    onValueChange?.(next);
  }

  function clear() {
    value = '';
    text = '';
    filtering = false;
    onValueChange?.('');
    input?.focus();
  }
</script>

{#if isReadonly}
  <!-- Read-only text keeps the name and still submits the value, as a read-only input would. -->
  <TextInput {...rest} id={inputId} value={selected?.label ?? ''} readonly disabled={isDisabled} />
  {#if name}<input type="hidden" {name} {value} disabled={isDisabled} />{/if}
{:else}
  <Combobox.Root
    type="single"
    bind:value
    bind:open
    {items}
    {name}
    inputValue={text}
    disabled={isDisabled}
    required={isRequired}
    allowDeselect={false}
    onValueChange={choose}
  >
    <div
      bind:this={box}
      class="field-control"
      data-invalid={isInvalid || undefined}
      data-disabled={isDisabled || undefined}
      data-state={open ? 'open' : undefined}
      data-preview={preview}
      {@attach pressFocuses(() => input)}
    >
      {#if prefix}
        <span class="field-control-icon"><Icon name={prefix} size={16} /></span>
      {/if}

      <Combobox.Input id={inputId} bind:ref={input} oninput={type}>
        {#snippet child({ props })}
          <input
            {...rest}
            {...props}
            class="field-control-input"
            autocomplete="off"
            aria-required={isRequired || undefined}
            aria-invalid={isInvalid || undefined}
            aria-describedby={idList(field?.describedBy, rest['aria-describedby'])}
          />
        {/snippet}
      </Combobox.Input>

      {#if showClear}
        <FieldButton icon="x" label={clearLabel} onclick={clear} />
      {/if}

      <!-- Out of the tab order, as the input opens the list itself with the arrow keys. -->
      <Combobox.Trigger>
        {#snippet child({ props })}
          <FieldButton {...props} icon="caret-down" label={showOptionsLabel} tabindex={-1} />
        {/snippet}
      </Combobox.Trigger>

      <span class="sr-only" role="status">{status}</span>
    </div>

    <ListboxPopup options={shown} anchor={box} emptyText={noMatchesText} {loading} {loadingText} />
  </Combobox.Root>
{/if}
