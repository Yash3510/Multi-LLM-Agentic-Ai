<script lang="ts">
  // The audit record (own-4ce look S10, features F39): how a released answer was produced, in
  // four figures, the chain of who did what, the evidence and an integrity check that a pasted
  // copy is the released answer (its SHA-256 against the fingerprint).
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { COPY_HOLD_MS, writeClipboard } from './clipboard';
  import Dialog from './Dialog.svelte';
  import Logomark from './Logomark.svelte';

  type Tone = 'plain' | 'good' | 'warn' | 'ink' | 'faint';

  type Props = {
    open?: boolean;
    outcome: 'released' | 'withheld';
    tries: number;
    externalCalls?: number;
    working: string;
    at: Date;
    chain: { role: string; text: string; time: string; tone?: Tone; model?: string }[];
    evidence: { index: number; title: string; cited: boolean }[];
    fingerprint: string;
  };

  let {
    open = $bindable(false),
    outcome,
    tries,
    externalCalls,
    working,
    at,
    chain,
    evidence,
    fingerprint,
  }: Props = $props();

  const when = $derived(
    new Intl.DateTimeFormat('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    }).format(at),
  );

  let copied = $state(false);
  let pasted = $state('');
  let verdict = $state<'match' | 'changed' | undefined>();

  const summary = $derived(
    [
      `Audit record, ${when}`,
      `Outcome: ${outcome === 'released' ? 'Released' : 'Withheld'} · Tries: ${tries} · Working time: ${working}`,
      ...chain.map(
        (row) => `${row.role.toUpperCase()}: ${row.text}${row.time ? ` (${row.time})` : ''}`,
      ),
      `Fingerprint: ${fingerprint}`,
    ].join('\n'),
  );

  async function copySummary() {
    if (await writeClipboard(summary)) {
      copied = true;
      setTimeout(() => (copied = false), COPY_HOLD_MS);
    }
  }

  function exportJson() {
    const record = {
      at: at.toISOString(),
      outcome,
      tries,
      externalCalls,
      working,
      chain,
      evidence,
      fingerprint,
    };
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' }),
    );
    const link = Object.assign(document.createElement('a'), {
      href: url,
      download: 'audit-record.json',
    });
    link.click();
    URL.revokeObjectURL(url);
  }

  async function verify() {
    const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(pasted));
    const hex = [...new Uint8Array(bytes)]
      .map((byte) => byte.toString(16).padStart(2, '0'))
      .join('');
    verdict = hex === fingerprint ? 'match' : 'changed';
  }
</script>

<Dialog bind:open title="Audit record" closeLabel="Close the audit record" size="wide">
  <div class="record">
    <div class="head">
      <Logomark size={22} />
      <span class="when">{when}</span>
      <span class="tools">
        <button type="button" class="pill" onclick={exportJson}>
          <Icon name="download-simple" size={14} />Export JSON
        </button>
        <button type="button" class="pill" onclick={copySummary}>
          {copied ? 'Copied' : 'Copy summary'}
        </button>
      </span>
    </div>

    <div class="tiles">
      <div class="tile">
        <span class="tile-label">Outcome</span>
        <span class="tile-value" data-tone={outcome === 'released' ? 'good' : 'warn'}>
          {outcome === 'released' ? 'Released' : 'Withheld'}
        </span>
      </div>
      <div class="tile">
        <span class="tile-label">Tries</span>
        <span class="tile-value">{tries}</span>
      </div>
      <div class="tile">
        <span class="tile-label">External calls</span>
        <span class="tile-value" data-tone={externalCalls ? 'warn' : undefined}>
          {externalCalls ?? '—'}
        </span>
      </div>
      <div class="tile">
        <span class="tile-label">Working time</span>
        <span class="tile-value">{working}</span>
      </div>
    </div>

    <h3 class="section">Chain</h3>
    <ol class="chain">
      {#each chain as row, index (index)}
        <li class="row" style:--index={index}>
          <span class="dot" data-tone={row.tone ?? 'plain'}></span>
          <span class="role">{row.role.toUpperCase()}</span>
          <span class="text" data-tone={row.tone}>
            {row.text}{#if row.model}<span class="model"> · {row.model}</span>{/if}
          </span>
          <span class="time">{row.time}</span>
        </li>
      {/each}
    </ol>

    <h3 class="section">Evidence</h3>
    {#if evidence.length}
      <ul class="evidence">
        {#each evidence as item (item.index)}
          <li>
            <span class="chip" data-cited={item.cited ? '' : undefined}
              >[{item.index}] {item.title}</span
            >
            <span class="how">{item.cited ? 'cited in the answer' : 'retrieved, not cited'}</span>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="how">No documents were retrieved for this answer.</p>
    {/if}

    <h3 class="section">Integrity</h3>
    <p class="integrity">This is the SHA-256 fingerprint of the released answer.</p>
    <code class="fingerprint">{fingerprint}</code>
    <form
      class="verify"
      onsubmit={(event) => {
        event.preventDefault();
        void verify();
      }}
    >
      <input
        class="field"
        bind:value={pasted}
        oninput={() => (verdict = undefined)}
        placeholder="Paste a copy of the answer to check it has not been changed"
        aria-label="Paste a copy of the answer to check it has not been changed"
      />
      <button type="submit" class="verify-button">Verify</button>
    </form>
    {#if verdict}
      <p class="result" data-verdict={verdict} role="status">
        {verdict === 'match'
          ? 'Matches the released answer.'
          : 'Does not match: the text has been changed.'}
      </p>
    {/if}
  </div>
</Dialog>

<style>
  .record {
    color: var(--color-gray-800);
  }

  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--spacing-2) var(--spacing-3);
  }

  .when {
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  .tools {
    display: flex;
    gap: 6px;
    margin-inline-start: auto;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px var(--spacing-3);
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-pill);
    color: var(--color-gray-800);
    font-size: var(--text-caption);
    font-weight: var(--font-weight-medium);
  }

  .pill:hover {
    background-color: var(--color-gray-50);
  }

  .tiles {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--spacing-2);
    margin-block-start: var(--spacing-4);
  }

  @media (min-width: 40rem) {
    .tiles {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
  }

  .tile {
    display: flex;
    flex-direction: column;
    padding: var(--spacing-2) var(--spacing-3);
    border-radius: 10px;
    background-color: var(--color-gray-50);
  }

  .tile-label {
    color: var(--color-gray-600);
    font-size: var(--text-tag);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .tile-value {
    color: var(--color-gray-900);
    font-size: var(--text-ui);
    font-weight: var(--font-weight-semibold);
    line-height: 20px;
  }

  .tile-value[data-tone='good'] {
    color: var(--color-emerald-700);
  }

  .tile-value[data-tone='warn'] {
    color: var(--color-amber-700);
  }

  .section {
    margin-block: var(--spacing-4) 6px;
    color: var(--color-gray-600);
    font-size: var(--text-tag);
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .chain {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding-block: 3.2px;
    font-size: 12.5px;
    line-height: 1.5;
    animation: rise 260ms ease-out calc(var(--index) * 35ms) both;
  }

  .dot {
    flex-shrink: 0;
    inline-size: 7px;
    block-size: 7px;
    translate: 0 7px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-400);
  }

  .dot[data-tone='warn'] {
    background-color: var(--color-amber-500);
  }

  .dot[data-tone='good'] {
    background-color: var(--color-emerald-500);
  }

  .dot[data-tone='ink'] {
    background-color: var(--color-gray-900);
  }

  .dot[data-tone='faint'] {
    background-color: var(--color-gray-300);
  }

  /* 64 px as measured; our role names are longer than the app's nicknames, so never wrap. */
  .role {
    flex-shrink: 0;
    min-inline-size: 64px;
    white-space: nowrap;
    color: var(--color-gray-900);
    font-size: var(--text-tag);
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
  }

  .text {
    flex: 1;
  }

  .text[data-tone='warn'] {
    color: var(--color-amber-700);
  }

  .text[data-tone='good'] {
    color: var(--color-emerald-700);
  }

  .model,
  .time {
    color: var(--color-gray-600);
  }

  .time {
    font-size: var(--text-micro);
    font-variant-numeric: tabular-nums;
  }

  .evidence {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
    font-size: 12.5px;
  }

  .evidence li {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-2);
  }

  .chip {
    padding-inline: var(--spacing-2);
    border: 1px dashed var(--color-gray-200);
    border-radius: var(--radius-pill);
    color: var(--color-gray-600);
    font-size: var(--text-micro);
    font-weight: var(--font-weight-medium);
    line-height: 18px;
  }

  .chip[data-cited] {
    border: 1px solid var(--color-gray-300);
    color: var(--color-gray-900);
  }

  .how {
    color: var(--color-gray-600);
    font-size: 12.5px;
  }

  .integrity {
    color: var(--color-gray-700);
    font-size: 12.5px;
  }

  .fingerprint {
    display: block;
    margin-block-start: var(--spacing-1);
    padding: var(--spacing-1) var(--spacing-2);
    border-radius: 8px;
    background-color: var(--color-gray-50);
    color: var(--color-gray-800);
    font-family: var(--font-mono);
    font-size: 11.5px;
    overflow-wrap: anywhere;
  }

  .verify {
    display: flex;
    gap: var(--spacing-2);
    margin-block-start: var(--spacing-2);
  }

  .field {
    flex: 1;
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--color-gray-200);
    border-radius: 10px;
    background: transparent;
    font-size: 12.5px;
  }

  .field::placeholder {
    color: var(--color-gray-400);
  }

  .field:focus {
    outline: none;
    border-color: var(--color-gray-400);
  }

  .verify-button {
    padding-inline: var(--spacing-4);
    border: 1px solid var(--color-gray-900);
    border-radius: var(--radius-pill);
    color: var(--color-gray-900);
    font-size: var(--text-caption);
    font-weight: var(--font-weight-medium);
  }

  .verify-button:hover {
    background-color: var(--color-gray-900);
    color: var(--color-white);
  }

  .result {
    margin-block-start: var(--spacing-2);
    font-size: 12.5px;
  }

  .result[data-verdict='match'] {
    color: var(--color-emerald-700);
  }

  .result[data-verdict='changed'] {
    color: var(--color-amber-700);
  }

  :is(.pill, .verify-button):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  @keyframes rise {
    from {
      opacity: 0;
      translate: 0 2px;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .row {
      animation: none;
    }
  }
</style>
