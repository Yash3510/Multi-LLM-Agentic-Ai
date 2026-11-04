<script module lang="ts">
  import type { SectionMeta } from '../section';

  // English until the ui_section_status and ui_status_* messages exist (requested); the captions
  // below are the same. Demo data is sector-neutral: rule R2, parameter Ratio, ids like CASE-0142.
  export const section: SectionMeta = {
    id: 'status',
    title: () => 'Status',
    description: () =>
      'Tags, counts, verdicts, receipt facts, the working dots, skeletons, empty states and inline alerts, in every state.',
  };
</script>

<script lang="ts">
  import { untrack } from 'svelte';
  import { m } from '$lib/i18n/generated/messages.js';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import Badge from '$lib/ui/components/Badge.svelte';
  import Button from '$lib/ui/components/Button.svelte';
  import EmptyState from '$lib/ui/components/EmptyState.svelte';
  import InlineAlert from '$lib/ui/components/InlineAlert.svelte';
  import Pill, { type CopyText } from '$lib/ui/components/Pill.svelte';
  import Skeleton from '$lib/ui/components/Skeleton.svelte';
  import StatusMark, { type Verdict } from '$lib/ui/components/StatusMark.svelte';
  import Tag from '$lib/ui/components/Tag.svelte';
  import WorkingDots from '$lib/ui/components/WorkingDots.svelte';
  import {
    formatDuration,
    formatMoney,
    formatNumber,
    formatQuantity,
    toIntlLocale,
  } from '$lib/ui/format';
  import ReplayButton from '../ReplayButton.svelte';
  import { replay } from '../replay.svelte';

  // The page is rebuilt when the locale changes, so reading it once is enough.
  const o = { locale: toIntlLocale(getLocale()) };

  const VERDICTS: Verdict[] = ['pass', 'review', 'fail', 'no-data', 'unverified'];
  const DECIDED: Verdict[] = ['pass', 'review', 'fail'];
  const FILES = [
    'summary.pdf',
    'ratios.xlsx',
    'brief.docx',
    'review.pptx',
    'export.csv',
    'notes.md',
  ];
  const HASH = '3f9a21c07be4d58e9a0c6f1b2d7e8a94c51f03b6d2e7a8c9f04b1d6e3a7c5b2f';
  const COPY: CopyText = {
    label: 'Copy fingerprint',
    done: 'Fingerprint copied',
    failed: 'Could not copy: the browser blocked the clipboard',
  };
  const PREVIEW = [
    { state: 'hover', caption: 'hover' },
    { state: 'focus', caption: 'focus-visible' },
    { state: 'active', caption: 'active' },
  ];
  const ROWS: { rule: string; parameter: string; value: string; verdict: Verdict }[] = [
    { rule: 'R2', parameter: 'Ratio', value: formatQuantity(82.5, '%', o), verdict: 'pass' },
    { rule: 'R3', parameter: 'Duration', value: formatDuration(12.4, o), verdict: 'review' },
    { rule: 'R4', parameter: 'Cost', value: formatMoney(1240.5, o), verdict: 'fail' },
    { rule: 'R5', parameter: 'Ratio', value: formatNumber(null, o), verdict: 'no-data' },
    { rule: 'R6', parameter: 'Ratio', value: formatQuantity(81.9, '%', o), verdict: 'unverified' },
  ];
  const DENSITIES = ['comfortable', 'default', 'compact'] as const;
  const STEPS = ['title', 'body', 'ui', 'small', 'caption'] as const;
  const STEP_CLASS = {
    title: 'text-title',
    body: 'text-body',
    ui: 'text-ui',
    small: 'text-small',
    caption: 'text-caption',
  };
  // Roughly the receipt facts' widths, so the skeleton's row wraps where the real one will.
  const FACT_WIDTHS = [7, 8.5, 10];

  // Replays remount the demos that only move once: the live verdicts and the delayed dots.
  let liveRun = $state(0);
  let dotsRun = $state(0);

  $effect(() => {
    if (replay.count > 0)
      untrack(() => {
        liveRun += 1;
        dotsRun += 1;
      });
  });

  // A run of R2 as it is seen live: the working dots while it checks, then the verdict draws in.
  // Each run takes the next of PASS, REVIEW and FAIL.
  let runs = $state(0);
  let checking = $state(false);
  let decided = $state<Verdict | undefined>();

  // Reloading the receipt shows its skeleton for as long as a slow answer would take.
  let reloading = $state(false);

  // Cleared when the section unmounts (a locale switch rebuilds the page), so no demo outlives it.
  const timers: ReturnType<typeof setTimeout>[] = [];
  $effect(() => () => timers.forEach(clearTimeout));

  function after(ms: number, then: () => void) {
    timers.push(setTimeout(then, ms));
  }

  function runR2() {
    checking = true;
    decided = undefined;
    after(1600, () => {
      decided = DECIDED[runs % DECIDED.length];
      runs += 1;
      checking = false;
    });
  }

  function reload() {
    reloading = true;
    after(2400, () => (reloading = false));
  }
</script>

<div class="flex flex-col gap-10">
  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Tag</h3>
    <dl class="rows">
      <div class="row">
        <dt>Neutral, control radius: a kind or a state of a document, never a verdict colour</dt>
        <dd>
          <Tag label="Draft" />
          <Tag label="Template" />
          <Tag label="Internal" />
        </dd>
      </div>
      <div class="row">
        <dt>File types: the extension in capitals</dt>
        <dd>
          {#each FILES as file (file)}
            <Tag {file} />
          {/each}
        </dd>
      </div>
      <div class="row">
        <dt>With a signature glyph for 4CE's own concepts</dt>
        <dd>
          <Tag label="Rule" icon="rule" />
          <Tag label="Pack" icon="pack" />
          <Tag label="Skill" icon="skill" />
        </dd>
      </div>
      <div class="row">
        <dt>A long label truncates at its container's edge</dt>
        <dd>
          <span class="narrow"><Tag label="Quarterly review template, second revision" /></span>
        </dd>
      </div>
      <div class="row">
        <dt>Hindi: no capitals and no tracking; matras stay whole</dt>
        <dd lang="hi">
          <Tag label="सूची" />
          <Tag label="टिप्पणी" />
          <Tag label="प्रतीक्षा" icon="rule" />
          <Tag file="सारांश.pdf" />
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Badge</h3>
    <dl class="rows">
      <div class="row">
        <dt>Counts, grouped in the active locale, tabular</dt>
        <dd>
          <Badge count={0} />
          <Badge count={7} />
          <Badge count={42} />
          <Badge count={1234} max={9999} />
          <Badge count={123456} max={999999} />
        </dd>
      </div>
      <div class="row">
        <dt>Capped past max, 99 unless set</dt>
        <dd>
          <Badge count={100} />
          <Badge count={1000} max={999} />
        </dd>
      </div>
      <div class="row">
        <dt>Beside its label. Outlined in ink when the count waits on a person</dt>
        <dd>
          <span class="inline-flex items-center gap-2 text-ui text-ink-1">
            {m.nav_cases()}
            <Badge count={12} label="12 cases" />
          </span>
          <span class="inline-flex items-center gap-2 text-ui text-ink-1">
            {m.nav_approvals()}
            <Badge count={2} tone="ink" label="2 waiting for sign-off" />
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>Hindi label, same figures</dt>
        <dd lang="hi">
          <span class="inline-flex items-center gap-2 text-ui text-ink-1">
            {m.nav_approvals({}, { locale: 'hi' })}
            <Badge count={2} tone="ink" />
          </span>
          <span class="inline-flex items-center gap-2 text-ui text-ink-1">
            {m.nav_chats({}, { locale: 'hi' })}
            <Badge count={128} />
          </span>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">StatusMark</h3>
    <dl class="rows">
      <div class="row">
        <dt>Plain: glyph plus word, for table cells and lines</dt>
        <dd>
          {#each VERDICTS as verdict (verdict)}
            <StatusMark {verdict} />
          {/each}
        </dd>
      </div>
      <div class="row">
        <dt>
          Badge: a status label on the verdict's soft fill. No data and could-not-check stay ink
        </dt>
        <dd>
          {#each VERDICTS as verdict (verdict)}
            <StatusMark {verdict} variant="badge" />
          {/each}
        </dd>
      </div>
      <div class="row">
        <dt>Live: the dots while R2 checks, then its verdict draws in once. Try it</dt>
        <dd>
          <Button
            variant="primary"
            icon="arrow-clockwise"
            disabled={checking}
            reason="R2 is running"
            onclick={runR2}
          >
            Run R2
          </Button>
          <span class="inline-flex h-6 items-center gap-2 text-small text-ink-2" aria-live="polite">
            {#if checking}
              <WorkingDots />
              Checking R2
            {:else if decided}
              R2
              <StatusMark verdict={decided} variant="badge" live />
            {/if}
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>Live draw-in of each decided verdict; under reduced motion, the final frame</dt>
        <dd>
          {#key liveRun}
            <span class="preview">
              <span class="inline-flex flex-wrap gap-3">
                {#each DECIDED as verdict (verdict)}
                  <StatusMark {verdict} variant="badge" live />
                {/each}
              </span>
              <span class="text-caption text-ink-3">motion</span>
            </span>
            <span class="preview" data-motion="reduce">
              <span class="inline-flex flex-wrap gap-3">
                {#each DECIDED as verdict (verdict)}
                  <StatusMark {verdict} variant="badge" live />
                {/each}
              </span>
              <span class="text-caption text-ink-3">reduced motion</span>
            </span>
          {/key}
          <ReplayButton label={m.ui_replay_one({ name: 'StatusMark' })} onclick={() => liveRun++} />
        </dd>
      </div>
      <div class="row">
        <dt>In a compact table: right-aligned tabular values, ids in Plex Mono</dt>
        <dd>
          <div class="w-full overflow-x-auto" data-density="compact">
            <table class="w-full border-collapse text-left">
              <thead class="bg-surface-sunken text-caption text-ink-3">
                <tr>
                  <th scope="col" class="h-row px-3 font-normal">Rule</th>
                  <th scope="col" class="h-row px-3 font-normal">Parameter</th>
                  <th scope="col" class="h-row px-3 text-end font-normal">Value</th>
                  <th scope="col" class="h-row px-3 font-normal">Verdict</th>
                </tr>
              </thead>
              <tbody>
                {#each ROWS as row (row.rule)}
                  <tr class="border-t border-line-1">
                    <th scope="row" class="h-row px-3 font-mono font-normal text-ink-1">
                      {row.rule}
                    </th>
                    <td class="h-row px-3 text-ink-2">{row.parameter}</td>
                    <td class="h-row px-3 text-end text-ink-1 tabular">{row.value}</td>
                    <td class="h-row px-3"><StatusMark verdict={row.verdict} /></td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Pill</h3>
    <dl class="rows">
      <div class="row">
        <dt>Receipt facts, read-only: tabular numbers, ids and versions in Plex Mono</dt>
        <dd>
          <Pill label="Case" value="CASE-0142" mono />
          <Pill label="Pack" value="core@1.4.0" mono />
          <Pill label="Ratio" value={82.5} unit="%" />
          <Pill label="Duration" value={formatDuration(65, o)} />
          <Pill label="Cost" value={formatMoney(1240.5, o)} />
          <Pill label="External calls" value={0} />
        </dd>
      </div>
      <div class="row">
        <dt>
          A hash shows 8 characters and copies all 64; paper prints them in groups of four. Try it
        </dt>
        <dd>
          <Pill label="Fingerprint" hash={HASH} copy={COPY} />
          <Pill
            label="Case"
            value="CASE-0142"
            mono
            copy={{ ...COPY, label: 'Copy case id', done: 'Case id copied' }}
          />
        </dd>
      </div>
      <div class="row">
        <dt>Copy button: hover, focus-visible, active, copied (held 1600 ms), refused</dt>
        <dd>
          {#each PREVIEW as { state, caption } (state)}
            <span class="preview" data-preview={state}>
              <Pill label="Fingerprint" hash={HASH} copy={COPY} />
              <span class="text-caption text-ink-3">{caption}</span>
            </span>
          {/each}
          <span class="preview">
            <Pill label="Fingerprint" hash={HASH} copy={COPY} copyStatus="done" />
            <span class="text-caption text-ink-3">copied</span>
          </span>
          <span class="preview">
            <Pill label="Fingerprint" hash={HASH} copy={COPY} copyStatus="failed" />
            <span class="text-caption text-ink-3">refused by the browser</span>
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>Empty: a missing value is a dash, with nothing to copy. A long value truncates</dt>
        <dd>
          <Pill label="Clause" value={null} copy={COPY} />
          <span class="narrow">
            <Pill label="Template" value="Quarterly review template, second revision" />
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>Hindi labels</dt>
        <dd>
          <Pill lang="hi" label="अवधि" value={3.74} unit="s" decimals={1} />
          <Pill lang="hi" label="मामला" value="CASE-0142" mono />
          <Pill lang="hi" label="फ़िंगरप्रिंट" hash={HASH} copy={COPY} />
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">WorkingDots</h3>
    <dl class="rows">
      <div class="row">
        <dt>Six violet dots, 14 px; the light walks round them once per ambient beat (3.8 s)</dt>
        <dd>
          <WorkingDots label="Working" />
          <span class="inline-flex items-center gap-2 text-small text-ink-2">
            <WorkingDots />
            Reader · reading 3 files
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>In a person's action it takes the action's ink, never violet; the label stays</dt>
        <dd>
          <Button loading>Export receipt</Button>
          <Button variant="primary" icon="download-simple" loading>Download receipt</Button>
        </dd>
      </div>
      <div class="row">
        <dt>Loading: appears only after 300 ms, its space kept meanwhile</dt>
        <dd>
          <span class="inline-flex items-center gap-2 text-small text-ink-2">
            {#key dotsRun}
              <WorkingDots delay={300} />
            {/key}
            Loading CASE-0142
          </span>
          <ReplayButton
            label={m.ui_replay_one({ name: 'WorkingDots' })}
            onclick={() => dotsRun++}
          />
        </dd>
      </div>
      <div class="row">
        <dt>Reduced motion: the still frame, six full dots</dt>
        <dd data-motion="reduce">
          <WorkingDots />
          <span class="inline-flex items-center gap-2 text-small text-ink-2">
            <WorkingDots />
            Reader · reading 3 files
          </span>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Skeleton</h3>
    <dl class="rows">
      <div class="row">
        <dt>Real line heights: each skeleton line beside the line of text that replaces it</dt>
        <dd>
          <div class="steps">
            {#each STEPS as step (step)}
              <span class="text-caption text-ink-3">{step}</span>
              <Skeleton {step} />
              <span class="truncate text-ink-1 {STEP_CLASS[step]}">CASE-0142 receipt</span>
            {/each}
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>
          Still for 300 ms, then one slow grey sheen per beat; nothing moves when the content lands
        </dt>
        <dd class="column">
          <div class="w-full" aria-busy={reloading}>
            {#if reloading}
              <div class="flex flex-col">
                <Skeleton step="title" last={40} />
                <Skeleton step="caption" last={30} />
                <div class="flex flex-wrap gap-2 pt-3">
                  {#each FACT_WIDTHS as width, index (index)}
                    <span class="flex" style="width: {width}rem">
                      <Skeleton block="pill" class="h-6 w-full" />
                    </span>
                  {/each}
                </div>
              </div>
            {:else}
              {@render receipt()}
            {/if}
          </div>
          <Button
            icon="arrow-clockwise"
            disabled={reloading}
            reason="The receipt is loading"
            onclick={reload}
          >
            Reload receipt
          </Button>
        </dd>
      </div>
      <div class="row">
        <dt>Blocks with real radii: a row, a tile, a thumbnail, a status label</dt>
        <dd class="blocks">
          <Skeleton block="control" class="h-row w-full" />
          <Skeleton block="inset" class="h-12 w-full" />
          <Skeleton block="control" class="size-8" />
          <Skeleton block="pill" class="h-6 w-full" />
        </dd>
      </div>
      <div class="row">
        <dt>Rows follow their region's density: 40, 32 and 28 px</dt>
        <dd class="blocks">
          {#each DENSITIES as density (density)}
            <div class="flex flex-col gap-1" data-density={density}>
              <Skeleton block="control" class="h-row w-full" />
              <span class="text-caption text-ink-3">{density}</span>
            </div>
          {/each}
        </dd>
      </div>
      <div class="row">
        <dt>Reduced motion: still, no sheen</dt>
        <dd class="blocks" data-motion="reduce">
          <Skeleton lines={2} />
          <Skeleton block="inset" class="h-12 w-full" />
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">EmptyState</h3>
    <dl class="rows">
      <div class="row">
        <dt>Signature glyph, a one-line title, what was checked, one action</dt>
        <dd>
          <div class="card">
            <EmptyState
              icon="observation"
              title="No readings yet"
              detail="Checked 3 uploaded files; none has a value for Ratio."
            >
              {#snippet action()}
                <Button variant="primary" icon="upload-simple">Upload files</Button>
              {/snippet}
            </EmptyState>
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>Lucide glyph, no action</dt>
        <dd>
          <div class="card">
            <EmptyState
              icon="magnifying-glass"
              title="No case matches CASE-0142"
              detail="Searched case ids, rule ids and hash prefixes."
            />
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>Hindi</dt>
        <dd>
          <div class="card">
            <EmptyState
              lang="hi"
              icon="ledger"
              title="अभी कोई प्रविष्टि नहीं"
              detail="पिछले 30 दिनों की सभी प्रविष्टियाँ जाँची गईं।"
            />
          </div>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">InlineAlert</h3>
    <dl class="rows">
      <div class="row">
        <dt>Info: neutral, never violet or green</dt>
        <dd class="stack">
          <InlineAlert
            >Values are shown in the units the pack gives; nothing is converted.</InlineAlert
          >
        </dd>
      </div>
      <div class="row">
        <dt>Caution, with a title; its action sits under the text, aligned with it</dt>
        <dd class="stack">
          <InlineAlert tone="caution" title="Needs a person">
            Ratio is 82.5 %, within 2 % of the limit in R2.
            {#snippet action()}
              <Button size="small" icon="arrow-up-right">Open R2</Button>
            {/snippet}
          </InlineAlert>
        </dd>
      </div>
      <div class="row">
        <dt>Stop: an error shown in place, announced at once, with one way forward</dt>
        <dd class="stack">
          <InlineAlert tone="stop" title="Draft not saved">
            The server did not answer. Nothing was changed.
            {#snippet action()}
              <Button size="small" icon="arrow-clockwise">Retry saving</Button>
            {/snippet}
          </InlineAlert>
        </dd>
      </div>
      <div class="row">
        <dt>Could not check: the unverified glyph, never shown as a pass</dt>
        <dd class="stack">
          <InlineAlert tone="caution" icon="unverified" title="Could not check">
            The ledger could not be reached, so CASE-0142 is not verified.
            {#snippet action()}
              <Button size="small" icon="arrow-clockwise">Check CASE-0142 again</Button>
            {/snippet}
          </InlineAlert>
        </dd>
      </div>
      <div class="row">
        <dt>Compact region: the text drops to the small step</dt>
        <dd class="stack" data-density="compact">
          <InlineAlert tone="caution">Ratio is within 2 % of the limit in R2.</InlineAlert>
        </dd>
      </div>
      <div class="row">
        <dt>Hindi</dt>
        <dd class="stack">
          <InlineAlert tone="caution" lang="hi" title="ध्यान दें">
            यह जाँच पूरी नहीं हो सकी। कृपया दोबारा प्रयास करें।
          </InlineAlert>
        </dd>
      </div>
    </dl>
  </div>
</div>

{#snippet receipt()}
  <div class="flex flex-col">
    <p class="text-title text-ink-1">CASE-0142 receipt</p>
    <p class="text-caption text-ink-3">R2 decided PASS on 8 Oct 2026</p>
    <div class="flex flex-wrap gap-2 pt-3">
      <Pill label="Ratio" value={82.5} unit="%" />
      <Pill label="Duration" value={formatDuration(65, o)} />
      <Pill label="Fingerprint" hash={HASH} copy={COPY} />
    </div>
  </div>
{/snippet}

<style>
  /* Caption on the left, examples on the right; stacked when narrow. */
  .rows {
    display: flex;
    flex-direction: column;
  }

  .row {
    display: grid;
    gap: var(--spacing-2) var(--spacing-6);
    padding-block: var(--spacing-3);
    border-top: 1px solid var(--color-line-1);
  }

  @media (min-width: 48rem) {
    .row {
      grid-template-columns: 14rem minmax(0, 1fr);
      align-items: center;
    }
  }

  dt {
    font-size: var(--text-caption);
    line-height: var(--text-caption--line-height);
    color: var(--color-ink-3);
  }

  dd {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--spacing-3);
    min-width: 0;
  }

  .narrow {
    display: flex;
    width: 10rem;
  }

  .preview {
    display: inline-flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-1);
  }

  .card {
    width: 100%;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-card);
    background-color: var(--color-surface-raised);
  }

  /* Step name, skeleton line, real line: each row is exactly one line box tall. */
  .steps {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) minmax(0, 1fr);
    gap: var(--spacing-2) var(--spacing-4);
    align-items: center;
    width: 100%;
  }

  /* Alerts take the full width, as they do in a panel or a form. */
  .stack {
    flex-direction: column;
    align-items: stretch;
  }

  .column {
    flex-direction: column;
    align-items: flex-start;
  }

  .blocks {
    display: grid;
    gap: var(--spacing-6);
    width: 100%;
  }

  @media (min-width: 48rem) {
    .blocks {
      grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
      align-items: end;
    }
  }
</style>
