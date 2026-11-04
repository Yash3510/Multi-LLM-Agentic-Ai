<script lang="ts">
  // The receipt under a released answer (own-4ce look S7, features F36-F37): labels saying how
  // the answer was produced, the fingerprint (click to copy) and the audit record, then what was
  // checked.
  import type { Receipt, SignOffRequest } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { formatTime } from '$lib/ui/format';
  import { COPY_HOLD_MS, writeClipboard } from './clipboard';

  type Props = { receipt: Receipt; checks: SignOffRequest['checks']; releasedAt?: Date };

  let { receipt, checks, releasedAt }: Props = $props();

  let copied = $state(false);
  const passed = $derived(checks.every((check) => check.verdict === 'pass'));

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
      <span class="label"
        ><b>Grounded</b> {receipt.sources} {receipt.sources === 1 ? 'source' : 'sources'}</span
      >
    {:else}
      <span class="label" data-tone="muted"><b>Not grounded</b> no documents used</span>
    {/if}
    <span class="label" data-tone={passed ? 'good' : 'warn'}>
      <b>Checked</b> Challenger {passed ? 'passed it' : 'failed it'}
    </span>
    {#if receipt.signedBy}
      <span class="label">
        <b>Released</b> by {receipt.signedBy}{releasedAt ? `, ${formatTime(releasedAt)}` : ''}
      </span>
    {/if}
    <button
      type="button"
      class="label fingerprint"
      title="SHA-256 of this answer's record. Click to copy."
      onclick={copy}
    >
      <b>{copied ? 'Copied' : 'Fingerprint'}</b> <code>{receipt.fingerprint.slice(0, 8)}</code>
    </button>
    <button type="button" class="label audit">
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

  .by {
    color: var(--color-gray-600);
    font-size: 9.5px;
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
</style>
