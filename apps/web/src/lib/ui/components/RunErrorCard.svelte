<script lang="ts">
  // The run error card (own-4ce look S6, features F28): a stopped run told plainly, with what
  // went wrong, where, how to fix it, a retry and the server's own words. It replaces the answer.
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { explainRunError } from '$lib/ui/run-error';
  import { COPY_HOLD_MS, writeClipboard } from './clipboard';

  type Props = {
    detail: string;
    advice?: string;
    /** The role the run stopped at, from the rail; 4CE when none. */
    role?: string;
    /** Offered only on the last message of a chat the person may regenerate in. */
    onretry?: () => void;
  };

  let { detail, advice, role, onretry }: Props = $props();

  const view = $derived(explainRunError({ detail, advice, role }));
  let retrying = $state(false);
  let open = $state(false);
  let copied = $state(false);

  async function copy() {
    if (view.command && (await writeClipboard(view.command))) {
      copied = true;
      setTimeout(() => (copied = false), COPY_HOLD_MS);
    }
  }
</script>

<div class="card">
  <div class="head">
    <span class="tile" aria-hidden="true"><Icon name={view.icon} size={16} /></span>
    <div>
      <h3 class="title">{view.title}</h3>
      <p class="subline">{view.subline}</p>
    </div>
  </div>
  <ol class="steps" data-numbered={view.steps.length > 1 ? '' : undefined}>
    {#each view.steps as step, index (index)}
      <li class="step">
        {#if view.steps.length > 1}<span class="badge">{index + 1}</span>{/if}
        <span>{step}</span>
      </li>
    {/each}
  </ol>
  {#if view.command}
    <div class="command">
      <code>{view.command}</code>
      <button type="button" class="copy" onclick={copy}>
        <Icon name={copied ? 'check' : 'copy'} size={14} />
        <span class="copy-label">{copied ? 'Copied' : 'Copy'}</span>
      </button>
    </div>
  {/if}
  <div class="actions">
    {#if onretry}
      <button
        type="button"
        class="retry"
        data-retrying={retrying ? '' : undefined}
        disabled={retrying}
        onclick={() => {
          retrying = true;
          onretry();
        }}
      >
        <span class="retry-icon"><Icon name="arrow-clockwise" size={14} /></span>
        {retrying ? 'Trying again' : 'Try again'}
      </button>
    {/if}
    <button type="button" class="detail-toggle" aria-expanded={open} onclick={() => (open = !open)}>
      <span class="caret" data-open={open ? '' : undefined}
        ><Icon name="caret-right" size={12} /></span
      >
      What the server said
    </button>
  </div>
  {#if open}
    <div class="detail"><pre>{detail}</pre></div>
  {/if}
</div>

<style>
  .card {
    max-inline-size: 40rem;
    margin-block: var(--spacing-1);
    padding: var(--spacing-4) 18px 14px;
    border: 1px solid var(--color-gray-100);
    border-radius: 16px;
    background-color: var(--color-white);
    animation: enter 300ms;
  }

  :global([data-theme='dark']) .card {
    border-color: var(--color-gray-800);
    background-color: var(--color-gray-900);
  }

  .head {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-3);
  }

  .tile {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 28px;
    block-size: 28px;
    border-radius: 10px;
    background-color: var(--color-amber-50);
    box-shadow: inset 0 0 0 1px var(--color-amber-100);
    color: var(--color-amber-600);
  }

  :global([data-theme='dark']) .tile {
    background-color: color-mix(in srgb, var(--color-amber-500) 10%, transparent);
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-amber-500) 15%, transparent);
    color: var(--color-amber-400);
  }

  .title {
    padding-block-start: 3px;
    color: var(--color-gray-900);
    font-size: var(--text-body);
    font-weight: var(--font-weight-medium);
    line-height: 1.375;
  }

  .subline {
    margin-block-start: 2px;
    color: var(--color-gray-600);
    font-size: 12.5px;
    line-height: 1.375;
  }

  :global([data-theme='dark']) .title {
    color: var(--color-gray-50);
  }

  :global([data-theme='dark']) .subline {
    color: var(--color-gray-400);
  }

  .steps {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin: var(--spacing-3) 0 0 40px;
  }

  .step {
    display: flex;
    gap: 10px;
    color: var(--color-gray-700);
    font-size: var(--text-ui);
    line-height: 1.55;
  }

  :global([data-theme='dark']) .step {
    color: var(--color-gray-300);
  }

  .badge {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 18px;
    block-size: 18px;
    translate: 0 3px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-100);
    color: var(--color-gray-600);
    font-size: var(--text-tag);
    font-variant-numeric: tabular-nums;
    font-weight: var(--font-weight-medium);
  }

  .command {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    margin: 10px 0 0 40px;
    padding: 6px 6px 6px var(--spacing-3);
    border-radius: var(--radius-inset);
    background-color: var(--color-gray-50);
    box-shadow: inset 0 0 0 1px var(--color-gray-100);
  }

  .command code {
    flex: 1;
    overflow: hidden;
    color: var(--color-gray-800);
    font-family: var(--font-mono);
    font-size: 12.5px;
    font-variant-ligatures: none;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .copy {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    padding: 4px var(--spacing-2);
    border-radius: 8px;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    font-weight: var(--font-weight-medium);
  }

  .copy:hover {
    background-color: color-mix(in srgb, var(--color-gray-200) 70%, transparent);
    color: var(--color-gray-900);
  }

  .copy-label {
    inline-size: 54.4px;
    text-align: start;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 14px 0 0 40px;
  }

  .retry {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 14px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-900);
    color: var(--color-white);
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
  }

  .retry:hover:not(:disabled) {
    background-color: var(--color-gray-800);
  }

  .retry:disabled {
    cursor: default;
  }

  .retry-icon {
    display: inline-flex;
    transition: rotate 500ms ease-out;
  }

  .retry:hover .retry-icon {
    rotate: -90deg;
  }

  .retry[data-retrying] .retry-icon {
    animation: spin 1s linear infinite;
  }

  :global([data-theme='dark']) .retry {
    background-color: var(--color-white);
    color: var(--color-gray-900);
  }

  .detail-toggle {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    padding: 7px var(--spacing-2);
    color: var(--color-gray-600);
    font-size: 12.5px;
  }

  .detail-toggle:hover {
    color: var(--color-gray-900);
  }

  .caret {
    display: inline-flex;
    transition: rotate 300ms ease-out;
  }

  .caret[data-open] {
    rotate: 90deg;
  }

  .detail {
    margin: 6px 0 0 40px;
    padding: var(--spacing-2) var(--spacing-3);
    border-radius: var(--radius-inset);
    background-color: var(--color-gray-50);
    animation: enter 240ms ease;
  }

  .detail pre {
    color: var(--color-gray-600);
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-variant-ligatures: none;
    line-height: 1.625;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }

  :is(.retry, .detail-toggle, .copy):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  @keyframes enter {
    from {
      opacity: 0;
    }
  }

  @keyframes spin {
    to {
      rotate: 1turn;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .card,
    .detail,
    .retry[data-retrying] .retry-icon {
      animation: none;
    }
  }
</style>
