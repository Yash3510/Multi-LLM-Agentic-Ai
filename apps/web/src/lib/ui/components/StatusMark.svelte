<script module lang="ts">
  import { m } from '$lib/i18n/generated/messages.js';
  import type { IconName } from '$lib/ui/icons/generated/icons';

  /** The Rule Engine's verdicts, plus "could not check", which is never shown as a pass. */
  export type Verdict = 'pass' | 'review' | 'fail' | 'no-data' | 'unverified';

  type Look = {
    glyph: IconName;
    word: () => string;
    /** The word's colour and, as a badge, its soft fill. */
    text: string;
    fill: string;
    /** The glyph's colour. */
    mark: string;
  };

  // Class names are written out in full so Tailwind finds them. NO DATA and "could not check" are
  // ink with dashed glyphs: dashes mean "not established", and neither is a verdict colour.
  export const LOOKS: Record<Verdict, Look> = {
    pass: {
      glyph: 'verdict-pass',
      word: m.verdict_pass,
      text: 'text-ok',
      fill: 'bg-ok-soft',
      mark: 'text-ok-mark',
    },
    review: {
      glyph: 'verdict-review',
      word: m.verdict_review,
      text: 'text-caution',
      fill: 'bg-caution-soft',
      mark: 'text-caution-mark',
    },
    fail: {
      glyph: 'verdict-fail',
      word: m.verdict_fail,
      text: 'text-stop',
      fill: 'bg-stop-soft',
      mark: 'text-stop-mark',
    },
    'no-data': {
      glyph: 'verdict-no-data',
      word: m.verdict_no_data,
      text: 'text-ink-1',
      fill: 'bg-gray-500/20',
      mark: 'text-ink-1',
    },
    unverified: {
      glyph: 'unverified',
      // Until a verdict_unverified message exists, the reference's wording for the glyph.
      word: m.ui_concept_unverified,
      text: 'text-ink-1',
      fill: 'bg-gray-500/20',
      mark: 'text-ink-1',
    },
  };
</script>

<script lang="ts">
  // A verdict as its glyph plus its word, never colour alone. The glyph is hidden from assistive
  // technology because the word says the same.
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    verdict: Verdict;
    /** plain: glyph and word, for table cells and lines. badge: on its soft fill, for headers and cards. */
    variant?: 'plain' | 'badge';
    /**
     * The verdict is arriving now, seen live: its glyph settles in once. Leave it off for anything
     * loaded from a record. Reduced motion shows the end.
     */
    live?: boolean;
  };

  let { verdict, variant = 'plain', live = false }: Props = $props();

  const look = $derived(LOOKS[verdict]);

  // Armed after mount, so a verdict that arrives live settles in even on first render.
  let drawing = $state(false);
  $effect.pre(() => {
    void verdict;
    drawing = false;
  });
  $effect(() => {
    void verdict;
    drawing = live;
  });
</script>

<!-- The status chip (ADR-0041 amendment): a full pill, the verdict's soft fill, 12 px medium. -->
<span
  class="inline-flex shrink-0 items-center gap-1.25 text-caption font-medium {look.text} {variant ===
  'badge'
    ? `h-6 rounded-pill ps-1.75 pe-2.25 ${look.fill}`
    : ''}"
>
  <span
    class="glyph inline-flex {look.mark}"
    class:drawing
    onanimationend={() => (drawing = false)}
  >
    <Icon name={look.glyph} size={14} />
  </span>
  {look.word()}
</span>

<style>
  .drawing {
    animation: settle 240ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  @keyframes settle {
    from {
      opacity: 0;
      scale: 0.6;
    }
  }
</style>
