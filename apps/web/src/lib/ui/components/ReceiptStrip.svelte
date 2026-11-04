<script lang="ts">
  // The receipt under a released answer (own-4ce look S7, features F36-F37): labels saying how
  // the answer was produced, the fingerprint (click to copy) and the audit record, then what was
  // checked, then the folds: full provenance, each agent's output and the execution timeline.
  import type { Receipt, SignOffRequest } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { renderMarkdown, safeHtml } from '$lib/ui/markdown';
  import { COPY_HOLD_MS, writeClipboard } from './clipboard';

  type Props = {
    receipt: Receipt;
    checks: SignOffRequest['checks'];
    releasedAt?: Date;
    /** The names of the sources the answer cites, for the Grounded label's hover. */
    cited?: string[];
    /** The run's status events with their offset from the start. */
    timeline?: { at: string; text: string }[];
    /** Opens the audit record. */
    onaudit?: () => void;
  };

  let { receipt, checks, releasedAt, cited = [], timeline = [], onaudit }: Props = $props();

  let open = $state<Record<string, boolean>>({});
  const reservations = $derived(checks.filter((check) => check.verdict === 'review').length);
  const clock = new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  });
  const folds = $derived([
    ...(receipt.folds ?? []),
    ...(timeline.length ? [{ title: 'Execution timeline', body: '' }] : []),
  ]);

  let copied = $state(false);
  const passed = $derived(checks.every((check) => check.verdict !== 'fail'));

  async function copy() {
    if (await writeClipboard(receipt.fingerprint)) {
      copied = true;
      setTimeout(() => (copied = false), COPY_HOLD_MS);
    }
  }
</script>

<div class="receipt" role="group" aria-label="How this answer was produced">
  <div class="labels">
    <span class="label"><b>Local</b> {receipt.model}</span>
    {#if receipt.sources > 0}
      <span
        class="label"
        data-label="grounded"
        title={cited.length ? cited.map((name) => `Cited: ${name}`).join('\n') : undefined}
        ><b>Grounded</b> {receipt.sources} {receipt.sources === 1 ? 'source' : 'sources'}</span
      >
    {:else}
      <span class="label" data-tone="muted"><b>Not grounded</b> no documents used</span>
    {/if}
    <span class="label" data-label="checked" data-tone={passed && !reservations ? 'good' : 'warn'}>
      <b>Checked</b> Challenger {passed ? 'passed it' : 'failed it'}{reservations
        ? `, ${reservations} ${reservations === 1 ? 'reservation' : 'reservations'}`
        : ''}
    </span>
    {#if receipt.signedBy}
      <span class="label">
        <b>Released</b> by {receipt.signedBy}{releasedAt ? `, ${clock.format(releasedAt)}` : ''}
      </span>
    {/if}
    <span class="label"><b>{Math.round(receipt.seconds)}s</b> working</span>
    {#if receipt.externalCalls !== undefined}
      <span class="label"
        ><b>{receipt.externalCalls}</b>
        {receipt.externalCalls === 1 ? 'external call' : 'external calls'}, observed</span
      >
    {/if}
    <button
      type="button"
      class="label fingerprint"
      title="SHA-256 of this answer's record. Click to copy."
      onclick={copy}
    >
      <b>{copied ? 'Copied' : 'Fingerprint'}</b> <code>{receipt.fingerprint.slice(0, 8)}</code>
    </button>
    <button type="button" class="label audit" onclick={onaudit}>
      <Icon name="file-text" size={12} /><b>Audit</b>
    </button>
  </div>
  {#if checks.length}
    <div class="checks">
      <h3 class="heading">What was checked</h3>
      <ul>
        {#each checks as check (check.label)}
          <li class="line">
            <span class="mark" data-verdict={check.verdict} aria-hidden="true">
              <Icon
                name={check.verdict === 'pass' ? 'check' : check.verdict === 'fail' ? 'x' : 'minus'}
                size={12}
              />
            </span>
            <span class="text">{check.label}</span>
            <span class="by">Challenger</span>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
  {#each folds as fold (fold.title)}
    <div class="fold">
      <button
        type="button"
        class="fold-toggle"
        aria-expanded={open[fold.title] ?? false}
        onclick={() => (open[fold.title] = !open[fold.title])}
      >
        {fold.title}
        <span class="caret" data-open={open[fold.title] ? '' : undefined}
          ><Icon name="sort-caret-down" size={12} /></span
        >
      </button>
      {#if open[fold.title]}
        {#if fold.title === 'Execution timeline'}
          <ol class="timeline">
            {#each timeline as step, index (index)}
              <li><span class="offset">{step.at}</span>{step.text}</li>
            {/each}
          </ol>
        {:else}
          <div class="fold-body" {@attach safeHtml(renderMarkdown(fold.body))}></div>
        {/if}
      {/if}
    </div>
  {/each}
</div>

<style>
  .receipt {
    margin-block: var(--spacing-2);
  }

  .labels {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .label {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    padding: 2px var(--spacing-2);
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-pill);
    background-color: var(--color-white);
    color: var(--color-gray-600);
    font-size: var(--text-micro);
    line-height: 16px;
  }

  .label b {
    font-weight: var(--font-weight-medium);
  }

  :global([data-theme='dark']) .label {
    border-color: var(--color-gray-800);
    background-color: var(--color-gray-900);
    color: var(--color-gray-300);
  }

  .label[data-tone='good'] {
    border-color: var(--color-emerald-200);
    color: var(--color-emerald-800);
  }

  .label[data-tone='warn'] {
    border-color: var(--color-amber-200);
    color: var(--color-amber-800);
  }

  .label[data-tone='muted'] {
    border-style: dashed;
  }

  .fingerprint {
    transition:
      border-color 150ms,
      color 150ms;
  }

  .fingerprint:hover {
    border-color: var(--color-gray-300);
    color: var(--color-gray-900);
  }

  .fingerprint code {
    font-family: var(--font-mono);
    font-size: var(--text-tag);
  }

  .audit {
    border-color: var(--color-gray-900);
    color: var(--color-gray-900);
  }

  .audit:hover {
    background-color: var(--color-gray-900);
    color: var(--color-white);
  }

  :is(.fingerprint, .audit):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .checks {
    margin-block-start: 10px;
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--color-gray-100);
    border-radius: 16px;
  }

  :global([data-theme='dark']) .checks {
    border-color: var(--color-gray-850);
  }

  .heading {
    margin-block-end: var(--spacing-1);
    color: var(--color-gray-600);
    font-size: var(--text-tag);
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  ul {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .line {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-2);
    color: var(--color-gray-700);
    font-size: 12.5px;
    line-height: 1.375;
  }

  :global([data-theme='dark']) .line {
    color: var(--color-gray-300);
  }

  .mark {
    display: inline-flex;
    translate: 0 3px;
    color: var(--color-amber-700);
  }

  .mark[data-verdict='pass'] {
    color: var(--color-emerald-700);
  }

  .text {
    flex: 1;
  }

  /* Folds (chat-messages look §5.5): 13.5 px muted toggles with a caret that turns. */
  .fold {
    margin-block-start: 6px;
  }

  .fold-toggle {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    padding-block: 3px;
    color: var(--color-gray-500);
    font-size: 13.5px;
    transition: color 150ms;
  }

  .fold-toggle:hover {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .fold-toggle {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .fold-toggle:hover {
    color: var(--color-gray-100);
  }

  .fold-toggle:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .caret {
    display: inline-flex;
    transition: rotate 300ms;
  }

  .caret[data-open] {
    rotate: 180deg;
  }

  .fold-body,
  .timeline {
    margin-block-end: 6px;
    color: var(--color-prose);
    font-size: var(--text-ui);
    line-height: 1.625;
  }

  .fold-body :global(table) {
    border-collapse: collapse;
    font-size: var(--text-small);
  }

  .fold-body :global(:is(th, td)) {
    padding: var(--spacing-1) var(--spacing-3);
    border-block-end: 1px solid var(--color-line-1);
    text-align: start;
  }

  .timeline {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: var(--text-small);
  }

  .offset {
    display: inline-block;
    min-inline-size: 4.5em;
    color: var(--color-gray-500);
    font-family: var(--font-mono);
    font-size: var(--text-caption);
  }

  .by {
    color: var(--color-gray-600);
    font-size: 9.5px;
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
</style>
