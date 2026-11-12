<script lang="ts">
  // The details under a released answer (ADR-0043): one panel with four tabs in place of five
  // separate rows. Provenance pairs each figure with its source and passage, Reasoning shows each
  // agent's own output, Timeline places every step on the run, and Sources says how each one was
  // used. Everything comes from the run's record (details.ts).
  import { Tabs } from 'bits-ui';
  import type { Receipt, SignOffRequest, Source } from '$lib/data';
  import {
    PROVENANCE,
    provenanceRows,
    reasoningSteps,
    sourceUses,
    timelineSpans,
  } from '$lib/ui/details';
  import { glide } from '$lib/ui/glide';
  import { renderMarkdown, safeHtml } from '$lib/ui/markdown';
  import './glide.css';

  type Props = {
    folds?: Receipt['folds'];
    sources?: Source[];
    checks?: SignOffRequest['checks'];
    /** The answer's text, to tell which sources it cites. */
    answer?: string;
    /** The run's status events, with their offset from its start. */
    steps?: { ms: number; stage: string; text: string }[];
    /** Opens a source's passage. */
    onopen?: (index: number) => void;
  };

  let { folds = [], sources = [], checks = [], answer = '', steps = [], onopen }: Props = $props();

  const provenance = $derived(folds.find((fold) => fold.title === PROVENANCE));
  const rows = $derived(provenance ? provenanceRows(provenance.body, sources) : []);
  const reasoning = $derived(reasoningSteps(folds));
  const spans = $derived(timelineSpans(steps));
  const uses = $derived(sourceUses(sources, checks, answer));
  const tabs = $derived(
    [
      { value: 'provenance', label: 'Provenance', count: rows.length, show: Boolean(provenance) },
      { value: 'reasoning', label: 'Reasoning', count: reasoning.length, show: reasoning.length },
      { value: 'timeline', label: 'Timeline', count: spans.length, show: spans.length },
      { value: 'sources', label: 'Sources', count: uses.length, show: uses.length },
    ].filter((tab) => tab.show),
  );
  let chosen = $state<string>();
  const value = $derived(tabs.some((tab) => tab.value === chosen) ? chosen : tabs[0]?.value);
  const percent = (part: number) => `${(part * 100).toFixed(2)}%`;
</script>

{#snippet ref(index: number, title?: string)}
  <button
    type="button"
    class="ref"
    aria-label={title ? `View source ${index}: ${title}` : `Source ${index}`}
    disabled={!title}
    onclick={() => onopen?.(index)}>{index}</button
  >
{/snippet}

{#if tabs.length}
  <section class="details" aria-label="Details of this answer">
    <Tabs.Root {value} onValueChange={(next) => (chosen = next)}>
      <Tabs.List class="details-tabs" aria-label="Details">
        {#snippet child({ props })}
          <div
            {...props}
            {@attach glide({ active: '.details-tab[data-state="active"]', hover: '.details-tab' })}
          >
            {#each tabs as tab (tab.value)}
              <Tabs.Trigger class="details-tab" value={tab.value}>
                {tab.label}{#if tab.count}<span class="count">{tab.count}</span>{/if}
              </Tabs.Trigger>
            {/each}
          </div>
        {/snippet}
      </Tabs.List>

      <Tabs.Content class="details-body" value="provenance">
        {#if rows.length}
          <div class="scroll">
            <table>
              <thead>
                <tr><th>Figure</th><th>Source</th><th>Passage</th></tr>
              </thead>
              <tbody>
                {#each rows as row (row.figure)}
                  <tr>
                    <td class="figure">{row.figure}</td>
                    <td>
                      {#each row.refs as source (source.index)}
                        <span class="cite">
                          {@render ref(source.index, 'title' in source ? source.title : undefined)}
                          {#if 'title' in source}<span>{source.title}</span>{/if}
                        </span>
                      {:else}
                        <span class="none">No source recorded</span>
                      {/each}
                    </td>
                    <td class="passage">
                      {#each row.refs as source (source.index)}
                        {#if 'passage' in source && source.passage}<q>{source.passage}</q>{/if}
                      {/each}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else if provenance}
          <div class="prose" {@attach safeHtml(renderMarkdown(provenance.body))}></div>
        {/if}
      </Tabs.Content>

      <Tabs.Content class="details-body" value="reasoning">
        <ol class="steps">
          {#each reasoning as step (step.role + step.step)}
            <li class="step">
              <span class="node" data-end aria-hidden="true"></span>
              <div class="head">
                <b>{step.role}</b>
                {#if step.step}<span class="what">{step.step}</span>{/if}
                {#if step.verdict}<span class="verdict" data-verdict={step.verdict}
                    >{step.verdict}</span
                  >{/if}
                {#if step.model}<span class="mono">{step.model}</span>{/if}
              </div>
              <div class="prose" {@attach safeHtml(renderMarkdown(step.body))}></div>
            </li>
          {/each}
        </ol>
      </Tabs.Content>

      <Tabs.Content class="details-body" value="timeline">
        <ol class="spans">
          {#each spans as span, index (index)}
            <li class="span">
              <span class="mono">{span.at}</span>
              <b>{span.role}</b>
              <span class="what">{span.text}</span>
              <span class="track" aria-hidden="true">
                <span
                  class="wire"
                  style:left={percent(span.start)}
                  style:right={percent(1 - span.end)}
                ></span>
                {#if span.end > span.start}<span class="node" style:left={percent(span.start)}
                  ></span>{/if}
                <span class="node" data-end style:left={percent(span.end)}></span>
              </span>
              <span class="mono took">{span.took ?? ''}</span>
            </li>
          {/each}
        </ol>
      </Tabs.Content>

      <Tabs.Content class="details-body" value="sources">
        <ul class="sources">
          {#each uses as source (source.index)}
            <li class="source">
              {@render ref(source.index, source.title)}
              <div class="about">
                <b>{source.title}</b>
                {#if source.passage}<q>{source.passage}</q>{/if}
                <span class="use"
                  >{[
                    source.cited ? 'Cited in the answer' : 'Not cited in the answer',
                    ...(source.supports.length ? [`Supports: ${source.supports.join('; ')}`] : []),
                  ].join(' · ')}</span
                >
              </div>
              <button type="button" class="open" onclick={() => onopen?.(source.index)}
                >Open<span class="sr-only"> source: {source.title}</span></button
              >
            </li>
          {/each}
        </ul>
      </Tabs.Content>
    </Tabs.Root>
  </section>
{/if}

<style>
  /* In the flow, so the soft fill and top highlight only: there is nothing behind it to blur. */
  .details {
    container-type: inline-size;
    margin-block: 10px var(--spacing-2);
    padding: 6px;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-panel);
    background-color: var(--glass-soft);
    box-shadow: var(--glass-edge);
    font-size: var(--text-small);
  }

  /* The marker slides between tabs and follows the pointer (glide.css). */
  .details :global(.details-tabs) {
    --glide-fill: var(--color-surface-raised);
    --glide-edge: var(--shadow-hairline);
    --glide-hover-fill: var(--color-tint);

    display: flex;
    gap: 2px;
    overflow-x: auto;
  }

  .details :global(.details-tab) {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-block-size: 30px;
    padding-inline: var(--spacing-3);
    border-radius: var(--radius-pill);
    color: var(--color-ink-3);
    font-weight: var(--font-weight-medium);
    white-space: nowrap;
    transition:
      color var(--duration-instant) var(--ease-out),
      background-color var(--duration-base) var(--ease-out);
  }

  .details :global(.details-tab:hover) {
    color: var(--color-ink-1);
  }

  .details :global(.details-tab[data-state='active']) {
    background-color: var(--color-surface-raised);
    box-shadow: var(--shadow-hairline);
    color: var(--color-ink-1);
  }

  @media (forced-colors: none) {
    .details :global([data-glide-host] .details-tab[data-state='active']) {
      background-color: transparent;
      box-shadow: none;
    }
  }

  .details :global(.details-tab:focus-visible) {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .count,
  .mono {
    color: var(--color-ink-3);
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    font-variant-numeric: tabular-nums;
  }

  /* Inner radius = panel radius minus the padding around it. */
  .details :global(.details-body) {
    margin-block-start: 6px;
    padding: var(--spacing-3) var(--spacing-4);
    border-radius: calc(var(--radius-panel) - 6px);
    background-color: var(--color-surface-raised);
    box-shadow: var(--shadow-hairline);
    color: var(--color-ink-2);
    line-height: 1.5;
  }

  .details :global(.details-body:focus-visible) {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  @media (prefers-reduced-motion: no-preference) {
    .details :global(.details-body) {
      transition:
        opacity var(--duration-base) var(--ease-out),
        translate var(--duration-calm) var(--ease-expo);
    }

    @starting-style {
      .details :global(.details-body) {
        opacity: 0;
        translate: 0 4px;
      }
    }
  }

  /* On a run answered here the panel follows the receipt's labels in. */
  :global([data-fresh]) .details {
    animation: details-in var(--duration-calm) var(--ease-out) 240ms both;
  }

  @keyframes details-in {
    from {
      opacity: 0;
      translate: 0 8px;
    }
  }

  b {
    color: var(--color-ink-1);
    font-weight: var(--font-weight-medium);
  }

  q {
    display: block;
    color: var(--color-ink-3);
  }

  .scroll {
    overflow-x: auto;
  }

  table {
    inline-size: 100%;
    border-collapse: collapse;
  }

  th {
    padding-block-end: var(--spacing-2);
    color: var(--color-ink-3);
    font-size: var(--text-tag);
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    text-align: start;
    text-transform: uppercase;
  }

  td {
    padding-block: var(--spacing-2);
    padding-inline-end: var(--spacing-4);
    border-block-start: 1px solid var(--color-line-1);
    vertical-align: top;
  }

  .figure {
    color: var(--color-ink-1);
    font-variant-numeric: tabular-nums;
    font-weight: var(--font-weight-medium);
    white-space: nowrap;
  }

  .cite {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .none {
    color: var(--color-ink-3);
  }

  .ref {
    display: inline-grid;
    flex: none;
    place-items: center;
    inline-size: 22px;
    block-size: 22px;
    border-radius: var(--radius-pill);
    background-color: var(--color-surface-hover);
    color: var(--color-ink-1);
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    transition: background-color var(--duration-instant) var(--ease-out);
  }

  .ref:enabled:hover,
  .open:hover {
    background-color: var(--color-ink-1);
    color: var(--color-surface-raised);
  }

  :is(.ref, .open):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .steps,
  .spans,
  .sources {
    display: flex;
    flex-direction: column;
  }

  /* The wire and its nodes, as on the stage rail: ink, never violet (ADR-0043 §4). */
  .node {
    box-sizing: border-box;
    inline-size: 9px;
    block-size: 9px;
    border: 1.5px solid var(--color-ink-1);
    border-radius: var(--radius-pill);
    background-color: var(--color-surface-raised);
  }

  .node[data-end] {
    background-color: var(--color-ink-1);
  }

  .step {
    position: relative;
    padding-block-end: var(--spacing-3);
    padding-inline-start: var(--spacing-6);
  }

  .step:last-child {
    padding-block-end: 0;
  }

  .step > .node {
    position: absolute;
    inset: 5px auto auto 0;
  }

  .step:not(:last-child)::before {
    position: absolute;
    inset: 16px auto 2px 4px;
    inline-size: 1px;
    background-color: var(--color-line-2);
    content: '';
  }

  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: var(--spacing-2);
  }

  .what {
    color: var(--color-ink-2);
  }

  .verdict {
    font-family: var(--font-mono);
    font-size: var(--text-tag);
    letter-spacing: 0.06em;
  }

  .verdict[data-verdict='PASS'] {
    color: var(--color-ok);
  }

  .verdict[data-verdict='FAIL'] {
    color: var(--color-stop);
  }

  .prose :global(table) {
    border-collapse: collapse;
  }

  .prose :global(:is(th, td)) {
    padding: var(--spacing-1) var(--spacing-3);
    border-block-end: 1px solid var(--color-line-1);
    text-align: start;
  }

  .span {
    display: grid;
    grid-template-columns: 52px 88px minmax(0, 1fr) minmax(120px, 30%) 40px;
    align-items: center;
    gap: var(--spacing-3);
    min-block-size: 32px;
  }

  .span + .span {
    border-block-start: 1px solid var(--color-line-1);
  }

  .track {
    position: relative;
    block-size: 9px;
    margin-inline: 5px;
  }

  .track::before,
  .wire {
    position: absolute;
    inset-block-start: 4px;
    block-size: 1px;
    content: '';
  }

  .track::before {
    inset-inline: 0;
    background-color: var(--color-line-2);
  }

  .wire {
    background-color: var(--color-ink-1);
  }

  .track .node {
    position: absolute;
    inset-block-start: 0;
    translate: -50% 0;
  }

  .took {
    text-align: end;
  }

  @container (max-width: 560px) {
    .span {
      grid-template-columns: 52px 88px minmax(0, 1fr) 40px;
    }

    .track {
      display: none;
    }
  }

  .source {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-3);
    padding-block: var(--spacing-2);
  }

  .source + .source {
    border-block-start: 1px solid var(--color-line-1);
  }

  .about {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 2px;
    min-inline-size: 0;
  }

  .use {
    color: var(--color-ink-3);
    font-size: var(--text-caption);
  }

  .open {
    padding: 3px var(--spacing-3);
    border-radius: var(--radius-pill);
    background-color: var(--color-surface-hover);
    color: var(--color-ink-1);
    font-size: var(--text-caption);
    font-weight: var(--font-weight-medium);
    transition: background-color var(--duration-instant) var(--ease-out);
  }
</style>
