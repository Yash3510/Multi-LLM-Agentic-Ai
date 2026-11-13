<script module lang="ts">
  import { m } from '$lib/i18n/generated/messages.js';
  import type { SectionMeta } from '../section';

  export const section: SectionMeta = {
    id: 'type',
    title: m.ui_section_type,
    description: m.ui_type_intro,
  };
</script>

<script lang="ts">
  import { formatHashFull, formatHashShort, formatNumber } from '$lib/ui/format';

  // Class names are written out in full so Tailwind finds them.
  const STEPS = [
    {
      step: 'micro',
      metrics: '11 / 16 · 500',
      use: m.ui_type_micro,
      class: 'text-micro',
      latin: 'Rule R2 · Review',
      devanagari: 'नियम R2 · समीक्षा',
    },
    {
      step: 'caption',
      metrics: '12 / 16 · 400',
      use: m.ui_type_caption,
      class: 'text-caption',
      latin: 'Updated 14:05 IST · CASE-0142',
      devanagari: 'अद्यतन 14:05 IST · CASE-0142',
    },
    {
      step: 'small',
      metrics: '13 / 20 · 400',
      use: m.ui_type_small,
      class: 'text-small',
      latin: 'Ratio 0.82 is inside the limit of 0.90',
      devanagari: 'अनुपात 0.82 सीमा 0.90 के भीतर है',
    },
    {
      step: 'ui',
      metrics: '14 / 20 · 400 / 500',
      use: m.ui_type_ui,
      class: 'text-ui',
      latin: 'Open the case',
      devanagari: 'केस खोलें',
    },
    {
      step: 'body',
      metrics: '15 / 24 · 400',
      use: m.ui_type_body,
      class: 'text-body',
      latin:
        'Every number goes through one format module, so a receipt, a ledger row and a printout show the same string.',
      devanagari:
        'हर संख्या एक ही फ़ॉर्मैट मॉड्यूल से होकर जाती है, ताकि रसीद, लेजर की पंक्ति और प्रिंट में एक जैसा पाठ दिखे।',
    },
    {
      step: 'title',
      metrics: '17 / 24 · 600',
      use: m.ui_type_title,
      class: 'text-title',
      latin: 'Case summary',
      devanagari: 'केस का सारांश',
    },
    {
      step: 'heading',
      metrics: '20 / 28 · 600',
      use: m.ui_type_heading,
      class: 'text-heading',
      latin: 'Cases',
      devanagari: 'केस',
    },
    {
      step: 'figure',
      metrics: '28 / 32 · 600',
      use: m.ui_type_figure,
      class: 'text-figure tabular',
      latin: formatNumber(123456),
      devanagari: `${formatNumber(42)} केस`,
    },
  ];

  const HASH = '3f9a21c07be4d58e9a0c6f1b2d7e8a94c51f03b6d2e7a8c9f04b1d6e3a7c5b2f';
  const FIGURES = [111111.1, 888888.8, 1234.5];
</script>

<div class="flex flex-col gap-8">
  <div class="type-table">
    <div class="type-head text-caption text-ink-3" aria-hidden="true">
      <span>{m.ui_type_step()}</span>
      <span>{m.ui_type_latin()}</span>
      <span>{m.ui_type_devanagari()}</span>
    </div>
    {#each STEPS as step (step.step)}
      <div class="type-row border-t border-line-1">
        <div class="type-meta flex flex-col gap-0.5">
          <code class="font-mono text-small text-ink-1">{step.step}</code>
          <span class="font-mono text-caption text-ink-3 tabular">{step.metrics}</span>
          <span class="text-caption text-ink-3">{step.use()}</span>
        </div>
        <p class="min-w-0 text-ink-1 {step.class}" lang="en">{step.latin}</p>
        <p class="min-w-0 text-ink-1 {step.class}" lang="hi">{step.devanagari}</p>
      </div>
    {/each}
  </div>

  <div class="grid gap-6 md:grid-cols-2">
    <div class="flex flex-col gap-2 rounded-inset border border-line-1 p-inset-card">
      <p class="text-caption text-ink-3">{m.ui_type_mono()}</p>
      <p class="font-mono text-small text-ink-1">CASE-0142 · R2 · {formatHashShort(HASH)}</p>
      <p class="font-mono text-caption text-ink-2">{formatHashFull(HASH)}</p>
    </div>
    <div class="flex flex-col gap-2 rounded-inset border border-line-1 p-inset-card">
      <p class="text-caption text-ink-3">{m.ui_type_figures()}</p>
      <div class="grid grid-cols-2 gap-4 text-small text-ink-1">
        <div class="flex flex-col items-end">
          {#each FIGURES as figure (figure)}
            <span class="tabular">{formatNumber(figure, { decimals: 1 })}</span>
          {/each}
          <span class="text-caption text-ink-3">{m.ui_type_tabular()}</span>
        </div>
        <div class="flex flex-col items-end">
          {#each FIGURES as figure (figure)}
            <span>{formatNumber(figure, { decimals: 1 })}</span>
          {/each}
          <span class="text-caption text-ink-3">{m.ui_type_proportional()}</span>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .type-head,
  .type-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    column-gap: var(--spacing-6);
    row-gap: var(--spacing-2);
  }

  .type-head {
    padding-block-end: var(--spacing-2);
  }

  .type-head > :first-child,
  .type-meta {
    grid-column: 1 / -1;
  }

  .type-row {
    align-items: baseline;
    padding-block: var(--spacing-4);
  }

  @media (min-width: 64rem) {
    .type-head,
    .type-row {
      grid-template-columns: calc(var(--spacing-12) * 4) minmax(0, 1fr) minmax(0, 1fr);
    }

    .type-head > :first-child,
    .type-meta {
      grid-column: auto;
    }
  }
</style>
