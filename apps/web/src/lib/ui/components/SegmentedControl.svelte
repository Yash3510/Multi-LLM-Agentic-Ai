<script lang="ts">
  // One choice from two to five short options, drawn as one strip: a view, a unit, a range, and the
  // worded on/off choice (OnOffChoice). It is a radio group (bits-ui): one tab stop, arrow keys move
  // and choose. The chosen segment sits on a raised thumb that slides along a faint track
  // (ADR-0041 amendment).
  import { RadioGroup } from 'bits-ui';
  import type { HTMLAttributes } from 'svelte/elements';
  import { getField, idList } from './field-context';
  import type { FieldOption } from './options';
  import './field-control.css';

  type Props = Omit<HTMLAttributes<HTMLDivElement>, 'children'> & {
    value?: string;
    options: readonly FieldOption[];
    /** For form submission. */
    name?: string;
    invalid?: boolean;
    disabled?: boolean;
    readonly?: boolean;
    required?: boolean;
    /** Segments share the width of the container instead of fitting their labels. */
    fill?: boolean;
    onValueChange?: (value: string) => void;
    /** Shows a state on the first segment without interaction, for the /ui reference. */
    preview?: 'hover' | 'focus' | 'active';
  };

  let {
    value = $bindable(''),
    options,
    name,
    invalid,
    disabled,
    readonly,
    required,
    fill = false,
    onValueChange,
    preview,
    ...rest
  }: Props = $props();

  const field = getField();

  const isDisabled = $derived(disabled ?? field?.disabled ?? false);
  const isReadonly = $derived(readonly ?? field?.readonly ?? false);
  const isInvalid = $derived(invalid ?? field?.invalid ?? false);
  const isRequired = $derived(required ?? field?.required ?? false);

  $effect(() => field?.adoptGroup());

  // The thumb follows the chosen segment: measured after each change and on resize.
  let strip = $state<HTMLDivElement>();
  let thumb = $state<{ x: number; width: number } | null>(null);
  $effect(() => {
    void value;
    if (!strip) return;
    const measure = () => {
      const on = strip?.querySelector<HTMLElement>('.segment[data-state="checked"]');
      thumb = on ? { x: on.offsetLeft, width: on.offsetWidth } : null;
    };
    measure();
    // Optional because jsdom, which component tests run in, has no ResizeObserver.
    const observer = globalThis.ResizeObserver ? new ResizeObserver(measure) : undefined;
    observer?.observe(strip);
    return () => observer?.disconnect();
  });
</script>

<RadioGroup.Root
  bind:value
  {name}
  orientation="horizontal"
  loop
  disabled={isDisabled}
  readonly={isReadonly}
  required={isRequired}
  {onValueChange}
>
  {#snippet child({ props })}
    <div
      {...rest}
      {...props}
      bind:this={strip}
      class={['segments', rest.class]}
      data-fill={fill || undefined}
      data-invalid={isInvalid || undefined}
      aria-labelledby={field?.labelId ?? rest['aria-labelledby']}
      aria-describedby={idList(field?.describedBy, rest['aria-describedby'])}
      aria-invalid={isInvalid || undefined}
      aria-required={isRequired || undefined}
      aria-disabled={isDisabled || undefined}
    >
      {#if thumb}
        <span
          class="thumb"
          aria-hidden="true"
          style="width: {thumb.width}px; transform: translateX({thumb.x}px)"
        ></span>
      {/if}
      {#each options as option, index (option.value)}
        <RadioGroup.Item value={option.value} disabled={option.disabled}>
          {#snippet child({ props: itemProps })}
            <button {...itemProps} class="segment" data-preview={index === 0 ? preview : undefined}>
              <span class="segment-label">{option.label}</span>
            </button>
          {/snippet}
        </RadioGroup.Item>
      {/each}
    </div>
  {/snippet}
</RadioGroup.Root>

<style>
  /* A faint track with a raised white thumb that slides to the chosen option (ADR-0041 amendment). */
  .segments {
    position: relative;
    display: inline-flex;
    max-width: 100%;
    padding: 3px;
    border-radius: 11px;
    background-color: var(--color-track);
  }

  .segments:not([data-fill]) {
    align-self: flex-start;
  }

  .segments[data-fill] {
    display: flex;
  }

  .segments[data-invalid] {
    box-shadow: 0 0 0 0.5px var(--color-stop-mark);
  }

  .thumb {
    position: absolute;
    inset-block: 3px;
    inset-inline-start: 0;
    border-radius: 8px;
    background-color: var(--color-surface-raised);
    box-shadow: var(--shadow-hairline);
    transition:
      transform 240ms cubic-bezier(0.4, 0, 0.2, 1),
      width 240ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .segment {
    position: relative;
    z-index: 1;
    display: inline-flex;
    flex: 0 1 auto;
    align-items: center;
    justify-content: center;
    min-width: 0;
    height: 26px;
    padding-inline: 12px;
    border-radius: 8px;
    color: var(--color-ink-3);
    font-size: var(--text-small);
    line-height: 20px;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
    transition: color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .segments[data-fill] .segment {
    flex: 1 1 0;
  }

  .segment-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .segment:is(:hover, [data-preview='hover']):not(
      [data-state='checked'],
      [data-disabled],
      [data-readonly]
    ) {
    color: var(--color-ink-1);
  }

  .segment:is(:focus-visible, [data-preview='focus']) {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .segment[data-state='checked'] {
    color: var(--color-ink-1);
    font-weight: var(--font-weight-medium);
  }

  .segment[data-readonly] {
    cursor: default;
  }

  .segment[data-disabled] {
    opacity: 0.45;
    cursor: not-allowed;
  }

  @media (forced-colors: active) {
    .segment[data-state='checked'] {
      background-color: Highlight;
      color: HighlightText;
    }
  }
</style>
