<script lang="ts">
  // The audit sheet (web-screens.md, /runs/[runId]/audit; design-system.md, Print; WP-UI-03,
  // part 3): a decided run as a printed A4 record. On screen it is a preview with one Print button;
  // in print only the sheet shows, black on white with 1 px rules.
  import { m } from '$lib/i18n/generated/messages.js';
  import AnswerBody from '$lib/ui/components/AnswerBody.svelte';
  import Link from '$lib/ui/components/Link.svelte';
  import Logomark from '$lib/ui/components/Logomark.svelte';
  import StageRail from '$lib/ui/components/StageRail.svelte';
  import { formatHashFull } from '$lib/ui/format';
  import { renderMarkdown } from '$lib/ui/markdown';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  const events = $derived(data.run.events);
  const decision = $derived(events.findLast((event) => event.type === 'decision'));
  const receipt = $derived(events.findLast((event) => event.type === 'receipt')?.receipt);
  const checks = $derived(events.findLast((event) => event.type === 'sign-off')?.request.checks);
  const sources = $derived(
    events.flatMap((event) => (event.type === 'source' ? [event.source] : [])),
  );
  const text = $derived(
    events.flatMap((event) => (event.type === 'delta' ? [event.text] : [])).join(''),
  );
  const verb = $derived(
    decision?.outcome === 'released' ? 'Released' : decision?.reason ? 'Returned' : 'Withheld',
  );

  const VERDICTS = { pass: 'PASS', review: 'REVIEW', fail: 'FAIL' } as const;
  const zoned = new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZoneName: 'short',
  });
  const printed = zoned.format(new Date());
  const named = (role: string) => role.charAt(0).toUpperCase() + role.slice(1);
  // A check's sources, by their titles: the clauses its verdict rests on.
  const clauses = (cites: number[] = []) =>
    cites.map((index) => sources.find((one) => one.index === index)?.title ?? `[${index}]`);
</script>

<svelte:head><title>{`Audit sheet: ${data.run.question} / ${m.app_name()}`}</title></svelte:head>

<div class="preview">
  {#if decision}
    <div class="bar">
      <Link href={`/runs/${data.run.id}`}>Back to the run</Link>
      <button type="button" class="print" onclick={() => window.print()}>Print</button>
    </div>
    <article class="sheet" aria-label="Audit sheet">
      <header class="head">
        <Logomark size={22} />
        {#if receipt?.classification}<p class="banner">{receipt.classification}</p>{/if}
        <span class="kind">Audit sheet</span>
      </header>
      <h1>{data.run.question}</h1>
      <StageRail {events} finished={data.run.finished} paced={false} />

      <section aria-labelledby="approval">
        <h2 id="approval">Approval</h2>
        <p>
          {verb} by {decision.by}, {zoned.format(new Date(decision.at))}{#if decision.reason}:
            {decision.reason}{/if}
        </p>
        {#if receipt}<p class="hash">{formatHashFull(receipt.fingerprint)}</p>{/if}
      </section>

      <section aria-labelledby="review">
        <h2 id="review">The review shown</h2>
        <AnswerBody html={renderMarkdown(text, sources)} oncite={() => {}} />
        {#if checks?.length}
          <ul class="checks">
            {#each checks as check (check.label)}
              <li>
                <b>{VERDICTS[check.verdict]}</b>
                {check.label}{#if check.cites?.length}: {clauses(check.cites).join('; ')}{/if}
              </li>
            {/each}
          </ul>
        {/if}
      </section>

      {#if receipt}
        <section aria-labelledby="record">
          <h2 id="record">Record</h2>
          <dl>
            {#if receipt.pack}
              <dt>Pack</dt>
              <dd>
                {receipt.pack.name}
                {receipt.pack.version}<span class="hash">{formatHashFull(receipt.pack.hash)}</span>
              </dd>
            {/if}
            {#if receipt.routing?.length}
              <dt>Models</dt>
              <dd>{receipt.routing.map((row) => `${named(row.role)} ${row.model}`).join(' · ')}</dd>
            {/if}
            <dt>External connections</dt>
            <dd>{receipt.externalCalls ?? 'Not observed'} during the run</dd>
          </dl>
        </section>
      {/if}

      <footer class="foot">
        Printed {printed}{#if data.user}
          by {data.user.name}{/if}{#if receipt?.ledger !== undefined}
          · Ledger entry {receipt.ledger}{/if}
      </footer>
    </article>
  {:else}
    <p class="empty">
      This run hasn't been decided yet, so it has no audit sheet.
      <Link href={`/runs/${data.run.id}`}>Open the run</Link>
    </p>
  {/if}
</div>

<style>
  /* On screen, a preview: the A4 sheet on the sunken ground. */
  .preview {
    flex: 1;
    padding: var(--spacing-6) var(--spacing-4) var(--spacing-12);
    background-color: var(--color-surface-sunken);
  }

  .bar,
  .sheet,
  .empty {
    max-inline-size: 210mm;
    margin-inline: auto;
  }

  .bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: var(--spacing-4);
    font-size: var(--text-small);
  }

  .print {
    padding: var(--spacing-1) var(--spacing-4);
    border: 1px solid var(--color-line-2);
    border-radius: var(--radius-pill);
    background-color: var(--color-surface-raised);
  }

  /* The paper is black on white in either theme, with 1 px rules and no fills (design system). */
  .sheet {
    box-sizing: border-box;
    min-block-size: 297mm;
    padding: 16mm;
    border: 1px solid var(--color-line-1);
    background-color: var(--ref-white);
    color: var(--ref-black);
    font-size: var(--text-small);
    line-height: 1.5;
  }

  .head {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    padding-block-end: var(--spacing-3);
    border-block-end: 1px solid var(--ref-black);
  }

  .banner {
    flex: 1;
    margin: 0;
    font-family: var(--font-mono);
    letter-spacing: 0.12em;
    text-align: center;
    text-transform: uppercase;
  }

  .kind {
    font-weight: var(--font-weight-medium);
  }

  h1 {
    margin-block: var(--spacing-4);
    font-size: var(--text-body);
    font-weight: var(--font-weight-medium);
  }

  section {
    padding-block: var(--spacing-3);
    border-block-start: 1px solid var(--ref-black);
  }

  h2 {
    margin: 0 0 var(--spacing-2);
    font-family: var(--font-mono);
    font-size: var(--text-tag);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .hash {
    display: block;
    font-family: var(--font-mono);
    overflow-wrap: anywhere;
  }

  .checks {
    margin: var(--spacing-2) 0 0;
    padding: 0;
    list-style: none;
  }

  .checks b {
    font-family: var(--font-mono);
    font-size: var(--text-tag);
  }

  dl {
    display: grid;
    grid-template-columns: max-content minmax(0, 1fr);
    gap: var(--spacing-1) var(--spacing-4);
    margin: 0;
  }

  dd {
    margin: 0;
  }

  .foot {
    padding-block-start: var(--spacing-3);
    border-block-start: 1px solid var(--ref-black);
    font-size: var(--text-caption);
  }

  /* In print only the sheet shows, A4 portrait, without the preview's frame. */
  @media print {
    :global(body *) {
      visibility: hidden;
    }

    .sheet,
    .sheet :global(*) {
      visibility: visible;
    }

    .sheet {
      position: absolute;
      inset: 0 auto auto 0;
      inline-size: 100%;
      min-block-size: 0;
      padding: 0;
      border: 0;
    }
  }

  @page {
    size: A4 portrait;
    margin: 16mm;
  }
</style>
