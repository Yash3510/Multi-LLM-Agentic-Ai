<script lang="ts">
  // A label, an optional description, the control, and an error message with its icon. The control
  // inside reads the ids and states from context (field-context.ts), so the wiring is never by hand:
  // label for=, aria-describedby, aria-invalid, aria-required, disabled and read-only.
  import { untrack, type Snippet } from 'svelte';
  import type { HTMLAttributes } from 'svelte/elements';
  import Icon from '../icons/Icon.svelte';
  import { idList, setField } from './field-context';
  import { fieldText } from './field-text';
  import './field-control.css';

  type Props = Omit<HTMLAttributes<HTMLDivElement>, 'children'> & {
    label?: string;
    description?: string;
    /** Shown below the control with an icon; also marks the control invalid. */
    error?: string;
    required?: boolean;
    disabled?: boolean;
    readonly?: boolean;
    /**
     * For radios, segments and checkbox lists: the label names the whole group instead of pointing
     * at one control, and each control keeps its own id. A checkbox list gets role="group" here;
     * RadioGroup and SegmentedControl are radio groups themselves and take the name over.
     */
    group?: boolean;
    /** The control's id; generated when left out. */
    id?: string;
    requiredLabel?: string;
    children: Snippet;
  };

  let {
    label,
    description,
    error,
    required = false,
    disabled = false,
    readonly = false,
    group = false,
    id,
    requiredLabel = fieldText.required(),
    children,
    ...rest
  }: Props = $props();

  const uid = $props.id();
  const controlId = $derived(id ?? `${uid}-control`);
  const labelId = `${uid}-label`;
  const requiredId = `${uid}-required`;
  const descriptionId = `${uid}-description`;
  const errorId = `${uid}-error`;

  const invalid = $derived(!!error);
  const describedBy = $derived(idList(description && descriptionId, invalid && errorId));

  // The last error stays in the collapsing row, so the text leaves with it instead of first.
  // A plain holder, not state: it only remembers what the derived last showed.
  const last = { error: '' };
  const shownError = $derived(error ? (last.error = error) : last.error);

  // A RadioGroup or SegmentedControl inside is the group itself (field-context.ts, adoptGroup).
  let adopters = $state(0);
  const wrapsGroup = $derived(group && adopters === 0);

  setField({
    get id() {
      return group ? undefined : controlId;
    },
    get labelId() {
      return label ? labelId : undefined;
    },
    get describedBy() {
      return describedBy;
    },
    get group() {
      return group;
    },
    get invalid() {
      return invalid;
    },
    get required() {
      return required;
    },
    get disabled() {
      return disabled;
    },
    get readonly() {
      return readonly;
    },
    // Untracked, so the adopting effect does not depend on the count it changes.
    adoptGroup() {
      untrack(() => (adopters += 1));
      return () => untrack(() => (adopters -= 1));
    },
  });
</script>

<div
  {...rest}
  class={['field', rest.class]}
  role={wrapsGroup ? 'group' : rest.role}
  aria-labelledby={wrapsGroup && label
    ? idList(labelId, required && requiredId)
    : rest['aria-labelledby']}
  aria-describedby={wrapsGroup ? describedBy : rest['aria-describedby']}
  data-disabled={disabled || undefined}
>
  {#if label || description}
    <div class="head">
      {#if label}
        <div class="label-row">
          {#if group}
            <span id={labelId} class="label">{label}</span>
          {:else}
            <label id={labelId} for={controlId} class="label">{label}</label>
          {/if}
          {#if required}
            <!-- A control says "required" itself (aria-required), so the word is for sight. A
                 checkbox list cannot, so its group name takes the word in through labelledby. -->
            <span id={requiredId} class="required" aria-hidden="true">{requiredLabel}</span>
          {/if}
        </div>
      {/if}
      {#if description}
        <p id={descriptionId} class="description">{description}</p>
      {/if}
    </div>
  {/if}

  {@render children()}

  <div class="message" data-open={invalid || undefined}>
    <div class="message-clip">
      <p id={errorId} class="error">
        <span class="error-icon"><Icon name="warning" size={16} /></span>
        <span>{shownError}</span>
      </p>
    </div>
  </div>
</div>

<style>
  .field {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  /* A 12.5 px medium label 6 px above the control, a 12 px muted description (ADR-0041 amendment). */
  .head {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-0_5);
    margin-block-end: var(--spacing-1_5);
  }

  .label-row {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: var(--spacing-1_5);
  }

  /* The size comes from the density region: ui, or small when compact. */
  .label {
    color: var(--color-ink-2);
    font-size: 12.5px;
    font-weight: var(--font-weight-medium);
    line-height: var(--field-line);
  }

  .required {
    color: var(--color-ink-3);
    font-size: var(--text-caption);
    line-height: var(--field-line-caption);
  }

  .description {
    color: var(--color-ink-3);
    font-size: var(--text-caption);
    line-height: var(--field-line);
  }

  .field[data-disabled] .head {
    opacity: 0.5;
  }

  /* Nothing jumps in height: the message row opens from 0fr to 1fr at calm. */
  .message {
    display: grid;
    grid-template-rows: 0fr;
    opacity: 0;
    visibility: hidden;
    transition-property: grid-template-rows, opacity, visibility;
    transition-duration: var(--duration-base);
    transition-timing-function: var(--ease-exit);
  }

  .message[data-open] {
    grid-template-rows: 1fr;
    opacity: 1;
    visibility: visible;
    transition-duration: var(--duration-calm);
    transition-timing-function: var(--ease-out);
  }

  .message-clip {
    min-height: 0;
    overflow: hidden;
  }

  .error {
    display: flex;
    gap: var(--spacing-1_5);
    padding-block-start: var(--spacing-1_5);
    color: var(--color-stop);
    font-size: var(--text-caption);
    line-height: var(--field-line);
  }

  /* The icon sits on the first line, whatever the script's line height. */
  .error-icon {
    display: inline-flex;
    align-items: center;
    height: 1lh;
    flex-shrink: 0;
  }
</style>
