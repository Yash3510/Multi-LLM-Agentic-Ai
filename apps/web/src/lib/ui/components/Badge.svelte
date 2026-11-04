<script module lang="ts">
  import { formatNumber } from '$lib/ui/format';

  /** The count as shown: grouped in the locale, and capped as "99+" past `max`. */
  export function countText(count: number, max: number, locale?: string): string {
    const whole = Math.max(0, Math.round(count));
    return whole > max
      ? `${formatNumber(max, { decimals: 0, locale })}+`
      : formatNumber(whole, { decimals: 0, locale });
  }
</script>

<script lang="ts">
  // A count beside a label: items found, items waiting. Neutral by default. `ink` marks a count that
  // waits on a person, drawn as the measured unread pill.
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import { toIntlLocale } from '$lib/ui/format';

  type Props = {
    count: number;
    /** Counts above this show as "max+". */
    max?: number;
    tone?: 'neutral' | 'ink';
    /** The whole meaning for assistive technology, e.g. "3 waiting for sign-off". */
    label?: string;
  };

  let { count, max = 99, tone = 'neutral', label }: Props = $props();

  // A soft count on the faint track; sky for a count that waits on a person (ADR-0037 amendment).
  const TONE = {
    neutral: 'bg-track text-ink-2',
    ink: 'bg-sky-500/10 text-sky-700 dark:bg-sky-400/12 dark:text-sky-300',
  };

  // The page is rebuilt when the locale changes, so reading it once is enough.
  const locale = toIntlLocale(getLocale());
  const text = $derived(countText(count, max, locale));
</script>

<span
  class="inline-flex h-4.5 min-w-4.5 shrink-0 items-center justify-center rounded-tight px-1.25 text-micro font-semibold tabular {TONE[
    tone
  ]}"
>
  {#if label}
    <span aria-hidden="true">{text}</span>
    <span class="sr-only">{label}</span>
  {:else}
    {text}
  {/if}
</span>
