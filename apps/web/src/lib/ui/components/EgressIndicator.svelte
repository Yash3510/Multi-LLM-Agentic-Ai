<script lang="ts">
  // The egress indicator in the chat top bar (own-4ce look S2): a pill with a dot and the count of
  // external connections, linking to the Sovereignty page. It renders nothing until a poll has
  // answered; the caller polls (every 3 s) once the egress API exists.
  import type { PathnameWithSearchOrHash } from '$app/types';
  import { resolve } from '$app/paths';
  import { m } from '$lib/i18n/generated/messages.js';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import { formatNumber, toIntlLocale } from '$lib/ui/format';

  type Props = {
    /** External connections seen by the last poll; undefined until one has answered. */
    external?: number;
    /** The last poll could not observe egress. */
    stale?: boolean;
    href?: PathnameWithSearchOrHash;
  };

  let { external, stale = false, href = '/#sovereignty' }: Props = $props();

  const locale = toIntlLocale(getLocale());
  const plural = new Intl.PluralRules(locale);
  const state = $derived(stale ? 'stale' : external ? 'alert' : 'clean');
  const label = $derived.by(() => {
    if (stale || external === undefined) return m.egress_stale_label();
    const count = formatNumber(external, { decimals: 0, locale });
    return plural.select(external) === 'one'
      ? m.egress_label_one({ count })
      : m.egress_label_other({ count });
  });
</script>

{#if external !== undefined}
  <a class="pill" href={resolve(href)} data-state={state} aria-label={label} title={label}>
    <span class="dot" aria-hidden="true"></span>
    {#if stale}
      <span>{m.egress_stale()}</span>
    {:else}
      <span class="count tabular">{formatNumber(external, { decimals: 0, locale })}</span>
      <span class="word">{m.egress_external()}</span>
    {/if}
  </a>
{/if}

<style>
  .pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    block-size: 24px;
    padding-inline: var(--spacing-2);
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-pill);
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    line-height: 16px;
    text-decoration: none;
    transition:
      color 150ms cubic-bezier(0.4, 0, 0.2, 1),
      border-color 150ms cubic-bezier(0.4, 0, 0.2, 1),
      background-color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .pill[data-state='clean']:hover {
    background-color: var(--color-gray-50);
  }

  .dot {
    inline-size: 6px;
    block-size: 6px;
    border-radius: var(--radius-pill);
    background-color: var(--color-emerald-500);
  }

  .pill[data-state='clean'] .dot {
    animation: breathe 2.4s ease-in-out infinite;
  }

  .count {
    font-weight: var(--font-weight-medium);
  }

  @media (max-width: 40rem) {
    .word {
      display: none;
    }
  }

  .pill[data-state='alert'] {
    border-color: var(--color-amber-300);
    background-color: var(--color-amber-50);
    color: var(--color-amber-800);
  }

  .pill[data-state='alert'] .dot {
    background-color: var(--color-amber-500);
  }

  .pill[data-state='stale'] {
    border-style: dashed;
    border-color: var(--color-gray-300);
    color: var(--color-gray-500);
  }

  .pill[data-state='stale'] .dot {
    background-color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .pill[data-state='clean'] {
    border-color: var(--color-gray-800);
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .pill[data-state='clean']:hover {
    background-color: var(--color-gray-850);
  }

  :global([data-theme='dark']) .pill[data-state='alert'] {
    border-color: var(--color-amber-800);
    background-color: color-mix(in srgb, var(--color-amber-950) 40%, transparent);
    color: var(--color-amber-300);
  }

  :global([data-theme='dark']) .pill[data-state='stale'] {
    border-color: var(--color-gray-700);
  }

  .pill:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  @keyframes breathe {
    50% {
      opacity: 0.35;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .pill[data-state='clean'] .dot {
      animation: none;
    }
  }
</style>
