<script lang="ts">
  // One choice from a few, all visible. bits-ui gives the radio group: one tab stop, arrow keys move
  // and choose, Space chooses, disabled options are skipped, a hidden input when a name is given.
  // In a group Field it is the group itself: named by the Field's label, described by its
  // description and error (field-context.ts, adoptGroup).
  import { RadioGroup } from 'bits-ui';
  import type { HTMLAttributes } from 'svelte/elements';
  import { getField, idList } from './field-context';
  import type { FieldOption } from './options';
  import './choice.css';
  import './field-control.css';

  type Props = Omit<HTMLAttributes<HTMLDivElement>, 'children'> & {
    value?: string;
    options: readonly FieldOption[];
    orientation?: 'vertical' | 'horizontal';
    /** For form submission. */
    name?: string;
    invalid?: boolean;
    disabled?: boolean;
    readonly?: boolean;
    required?: boolean;
    onValueChange?: (value: string) => void;
    /** Shows a state on the first option without interaction, for the /ui reference. */
    preview?: 'hover' | 'focus' | 'active';
  };

  let {
    value = $bindable(''),
    options,
    orientation = 'vertical',
    name,
    invalid,
    disabled,
    readonly,
    required,
    onValueChange,
    preview,
    ...rest
  }: Props = $props();

  const field = getField();
  const uid = $props.id();

  const isDisabled = $derived(disabled ?? field?.disabled ?? false);
  const isReadonly = $derived(readonly ?? field?.readonly ?? false);
  const isInvalid = $derived(invalid ?? field?.invalid ?? false);
  const isRequired = $derived(required ?? field?.required ?? false);

  $effect(() => field?.adoptGroup());
</script>

<RadioGroup.Root
  bind:value
  {name}
  {orientation}
  disabled={isDisabled}
  readonly={isReadonly}
  required={isRequired}
  {onValueChange}
>
  {#snippet child({ props })}
    <div
      {...rest}
      {...props}
      class={['radios', rest.class]}
      aria-labelledby={field?.labelId ?? rest['aria-labelledby']}
      aria-describedby={idList(field?.describedBy, rest['aria-describedby'])}
      aria-invalid={isInvalid || undefined}
      aria-required={isRequired || undefined}
      aria-disabled={isDisabled || undefined}
    >
      {#each options as option, index (option.value)}
        {@const off = isDisabled || option.disabled}
        <label
          class="choice"
          data-disabled={off || undefined}
          data-readonly={isReadonly || undefined}
        >
          <span class="choice-slot">
            <RadioGroup.Item value={option.value} disabled={option.disabled}>
              {#snippet child({ props: itemProps })}
                <button
                  {...itemProps}
                  class="choice-mark ring"
                  data-invalid={isInvalid || undefined}
                  data-preview={index === 0 ? preview : undefined}
                  aria-labelledby="{uid}-{index}-label"
                  aria-describedby={option.description ? `${uid}-${index}-description` : undefined}
                ></button>
              {/snippet}
            </RadioGroup.Item>
          </span>
          <span class="choice-text">
            <span id="{uid}-{index}-label" class="choice-label">{option.label}</span>
            {#if option.description}
              <span id="{uid}-{index}-description" class="choice-description">
                {option.description}
              </span>
            {/if}
          </span>
        </label>
      {/each}
    </div>
  {/snippet}
</RadioGroup.Root>

<style>
  .radios {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .radios[data-orientation='horizontal'] {
    flex-direction: row;
    flex-wrap: wrap;
    column-gap: var(--spacing-5);
  }

  /* 16 px, the check box's look. Chosen: solid fill with an inverse dot. */
  .ring {
    width: 16px;
    height: 16px;
    border-radius: var(--radius-pill);
  }

  .ring[data-state='checked']::before {
    content: '';
    width: var(--spacing-1_5);
    height: var(--spacing-1_5);
    border-radius: var(--radius-pill);
    background-color: currentColor;
  }
</style>
