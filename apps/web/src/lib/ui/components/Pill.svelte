<script module lang="ts">
  export type CopyStatus = 'idle' | 'done' | 'failed';

  /** Strings for the copy affordance, in the active locale. */
  export interface CopyText {
    /** The button's accessible name and its hint, e.g. "Copy fingerprint". */
    label: string;
    /** Shown in the hint and announced once the value is on the clipboard. */
    done: string;
    /** Shown in the hint and announced when the browser refuses. */
    failed: string;
  }
</script>

<script lang="ts">
  // One fact of a record as label and value: a case id, a pack version, a duration, a fingerprint.
  // Read-only, so it sits on the sunken fill; numbers are tabular. A hash shows its first 8
  // characters on screen and all 64 in groups of four on paper, and copies the raw 64.
  import { Tooltip } from 'bits-ui';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import { DURATION, fade } from '$lib/ui/motion.svelte';
  import {
    MISSING,
    formatHashFull,
    formatHashShort,
    formatNumber,
    formatQuantity,
    toIntlLocale,
  } from '$lib/ui/format';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { COPY_HOLD_MS, writeClipboard } from './clipboard';

  type Props = {
    label: string;
    /** A number is formatted in the active locale, with `unit` joined by a narrow no-break space. */
    value?: string | number | null;
    unit?: string;
    /** Fixed decimals for a number. */
    decimals?: number;
    /** A hash: 8 characters and an ellipsis on screen, in Plex Mono. */
    hash?: string;
    /** Identifiers (ids, versions) in Plex Mono. Hashes always are. */
    mono?: boolean;
    /** Adds the copy button: it copies the full hash, or the value as written. */
    copy?: CopyText;
    /** The copy feedback, bindable. It returns to idle after 1600 ms. */
    copyStatus?: CopyStatus;
    /** The label's language when it differs from the page's. */
    lang?: string;
  };

  let {
    label,
    value,
    unit,
    decimals,
    hash,
    mono = false,
    copy,
    copyStatus = $bindable('idle'),
    lang,
  }: Props = $props();

  // The page is rebuilt when the locale changes, so reading it once is enough.
  const locale = toIntlLocale(getLocale());

  const shown = $derived.by(() => {
    if (hash !== undefined) return formatHashShort(hash);
    if (typeof value === 'number') {
      return unit
        ? formatQuantity(value, unit, { decimals, locale })
        : formatNumber(value, { decimals, locale });
    }
    return value?.trim() || MISSING;
  });

  const raw = $derived(hash?.trim() || (typeof value === 'string' ? value.trim() : ''));
  const hint = $derived(
    copyStatus === 'done' ? copy?.done : copyStatus === 'failed' ? copy?.failed : copy?.label,
  );

  let timer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => () => clearTimeout(timer));

  async function onCopy() {
    copyStatus = (await writeClipboard(raw)) ? 'done' : 'failed';
    clearTimeout(timer);
    timer = setTimeout(() => (copyStatus = 'idle'), COPY_HOLD_MS);
  }
</script>

<span
  class="pill inline-flex h-6 max-w-full min-w-0 items-center gap-1.5 rounded-pill border border-line-1 bg-surface-sunken ps-2 text-caption"
  class:pe-2={!(copy && raw)}
>
  <span class="shrink-0 text-ink-3" {lang}>{label}</span>
  <span class="value truncate text-ink-1 tabular" class:font-mono={mono || hash !== undefined}>
    {#if hash !== undefined && raw}
      <span class="short">{shown}</span><span class="full">{formatHashFull(raw)}</span>
    {:else}
      {shown}
    {/if}
  </span>
  {#if copy && raw}
    <!-- Icon-only, so the name is also a hint on hover and keyboard focus; it says "Copied" while the tick holds. -->
    <Tooltip.Provider delayDuration={DURATION.slow} disableCloseOnTriggerClick>
      <Tooltip.Root>
        <Tooltip.Trigger onclick={onCopy}>
          {#snippet child({ props })}
            <!-- The hint repeats the name, so it is not also the button's description. -->
            <button
              {...props}
              type="button"
              class="copy"
              aria-label={copy.label}
              aria-describedby={undefined}
            >
              {#key copyStatus}
                <span class="inline-flex" in:fade={{ duration: DURATION.quick }}>
                  {#if copyStatus === 'done'}
                    <Icon name="check" size={16} />
                  {:else if copyStatus === 'failed'}
                    <span class="inline-flex text-stop"><Icon name="warning" size={16} /></span>
                  {:else}
                    <Icon name="copy" size={16} />
                  {/if}
                </span>
              {/key}
            </button>
          {/snippet}
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            data-pill-hint=""
            sideOffset={6}
            collisionPadding={8}
            class="rounded-control border border-line-1 bg-surface-raised px-2 py-1 text-caption text-ink-1 shadow-e2"
          >
            {hint}
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
    <!-- Present from the start, so the change is announced. -->
    <span class="sr-only" role="status">
      {copyStatus === 'done' ? copy.done : copyStatus === 'failed' ? copy.failed : ''}
    </span>
  {/if}
</span>

<style>
  /*
   * A 24 px round button that covers the pill's end cap, border included, so the hit target is a
   * full 24 x 24 inside a 24 px pill. The pill is already sunken, so hover takes the line-1 step
   * (the hover surface would barely show on it) and press one step darker, as the field buttons
   * do. Focus is the global outline. An ancestor's data-preview shows each state still, for /ui.
   */
  .copy {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    width: var(--spacing-6);
    height: var(--spacing-6);
    margin-block: -1px;
    margin-inline-end: -1px;
    border-radius: var(--radius-pill);
    color: var(--color-ink-2);
    cursor: pointer;
    transition-property: background-color, color;
    transition-duration: var(--duration-quick);
    transition-timing-function: var(--ease-out);
  }

  .copy:hover,
  :global([data-preview='hover']) .copy {
    background-color: var(--color-line-1);
    color: var(--color-ink-1);
  }

  .copy:active,
  :global([data-preview='active']) .copy {
    background-color: var(--color-line-2);
    color: var(--color-ink-1);
    transition-duration: var(--duration-instant);
  }

  :global([data-preview='focus']) .copy {
    outline: 2px solid var(--color-focus);
    outline-offset: var(--focus-offset, 2px);
  }

  .full {
    display: none;
  }

  /* The hint fades at base and leaves in two thirds of that; reduced motion caps both at 120 ms. */
  :global([data-pill-hint]) {
    transition: opacity var(--duration-base) var(--ease-out);
  }

  :global([data-pill-hint][data-starting-style]),
  :global([data-pill-hint][data-ending-style]) {
    opacity: 0;
  }

  :global([data-pill-hint][data-ending-style]) {
    transition-duration: calc(var(--duration-base) * 2 / 3);
    transition-timing-function: var(--ease-exit);
  }

  /* Paper shows the whole fingerprint in groups of four, wrapping between groups; nothing to press. */
  @media print {
    .pill {
      height: auto;
    }

    .value {
      overflow: visible;
      white-space: normal;
    }

    .short,
    .copy {
      display: none;
    }

    .full {
      display: inline;
    }
  }
</style>
