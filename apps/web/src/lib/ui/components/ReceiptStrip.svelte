<script lang="ts">
  // The receipt under a released answer (own-4ce look S7, features F36-F37): labels saying how
  // the answer was produced, the fingerprint (click to copy) and the audit record, then what was
  // checked. The provenance, each agent's output and the timeline are in DetailsPanel.
  import type { Receipt, Revision, SignOffRequest } from '$lib/data';
  import RevisionCard from './RevisionCard.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { COPY_HOLD_MS, writeClipboard } from './clipboard';

  type Props = {
    receipt: Receipt;
    checks: SignOffRequest['checks'];
    releasedAt?: Date;
    /** The names of the sources the answer cites, for the Grounded label's hover. */
    cited?: string[];
    /** Opens the audit record. */
    onaudit?: () => void;
    /** What changed on a later try, shown above the checks. */
    revision?: Revision;
  };

  let { receipt, checks, releasedAt, cited = [], onaudit, revision }: Props = $props();

  const reservations = $derived(checks.filter((check) => check.verdict === 'review').length);
  const clock = new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  });

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
    <span class="label" data-label="model"><b>Local</b> {receipt.model}</span>
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
  {#if revision}<RevisionCard {revision} {passed} />{/if}
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

  /* On a run answered here the labels arrive one after another, 40 ms apart. */
  :global([data-fresh]) .label {
    animation: label-in var(--duration-calm) var(--ease-out) both;
  }

  :global([data-fresh]) .label:nth-child(2) {
    animation-delay: 40ms;
  }

  :global([data-fresh]) .label:nth-child(3) {
    animation-delay: 80ms;
  }

  :global([data-fresh]) .label:nth-child(4) {
    animation-delay: 120ms;
  }

  :global([data-fresh]) .label:nth-child(5) {
    animation-delay: 160ms;
  }

  :global([data-fresh]) .label:nth-child(n + 6) {
    animation-delay: 200ms;
  }

  :global([data-fresh]) .checks {
    animation: label-in var(--duration-calm) var(--ease-out) 200ms both;
  }

  @keyframes label-in {
    from {
      opacity: 0;
      translate: 0 6px;
    }
  }

  .label b {
    font-weight: var(--font-weight-medium);
  }

  /* The model is a machine value, so it is set in mono; its "Local" stays in the text face. */
  .label[data-label='model'] {
    font-family: var(--font-mono);
  }

  .label[data-label='model'] b {
    font-family: var(--font-sans);
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

  /* Dark: the verdict green that passes AA on the dark ground (polish pass, WP-F-10). */
  :global([data-theme='dark']) .label[data-tone='good'] {
    border-color: color-mix(in srgb, var(--color-ok) 35%, transparent);
    color: var(--color-ok);
  }

  .label[data-tone='warn'] {
    border-color: var(--color-amber-200);
    color: var(--color-amber-800);
  }

  .label[data-tone='muted'] {
    border-style: dashed;
  }

  :is(.fingerprint, .audit) {
    transition:
      background-color var(--duration-base) var(--ease-out),
      border-color var(--duration-base) var(--ease-out),
      color var(--duration-base) var(--ease-out);
  }

  :is(.fingerprint, .audit):hover {
    transition-duration: var(--duration-instant);
  }

  .fingerprint:hover {
    border-color: var(--color-line-2);
    background-color: var(--color-surface-hover);
    color: var(--color-ink-1);
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
    border-radius: var(--radius-checks);
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

  .by {
    color: var(--color-gray-600);
    font-size: 9.5px;
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
</style>
