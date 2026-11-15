<script lang="ts">
  // A run's tool calls as one quiet fold-out line: a leading status (a travelling light while a
  // call runs, a grey tick when all are done, a red cross on failure), the tool names in mono and
  // a summary, then each call's input and output when opened.
  import Wire from './Wire.svelte';
  import type { ToolCall } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';

  let { calls }: { calls: ToolCall[] } = $props();

  let open = $state(false);
  const status = $derived(
    calls.some((call) => call.state === 'running')
      ? 'running'
      : calls.some((call) => call.state === 'failed')
        ? 'failed'
        : 'done',
  );
  const names = $derived([...new Set(calls.map((call) => call.name))].join(', '));
</script>

<div class="group">
  <button
    type="button"
    class="toggle"
    data-state={status}
    aria-label="Toggle details"
    aria-expanded={open}
    onclick={() => (open = !open)}
  >
    <span class="lead" aria-hidden="true">
      {#if status === 'running'}
        <Wire width={14} />
      {:else if status === 'failed'}
        <Icon name="tools-failed" size={14} />
      {:else}
        <Icon name="tools-done" size={14} />
      {/if}
    </span>
    <span class="text">
      <span class="label" data-running={status === 'running' ? '' : undefined}>{names}</span>
      <span class="summary">{calls.length === 1 ? '1 call' : `${calls.length} calls`}</span>
    </span>
    <span class="caret" aria-hidden="true">
      <Icon name={open ? 'caret-up' : 'sort-caret-down'} size={12} />
    </span>
  </button>
  {#if open}
    <ul class="calls">
      {#each calls as call (call.id)}
        <li class="call">
          <span class="call-name">{call.name}</span>
          <span class="call-input">{call.input}</span>
          {#if call.output}<span class="call-output">→ {call.output}</span>{/if}
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .group {
    inline-size: 100%;
    margin-block-end: 6px;
  }

  /* As wide as its text, so the caret sits beside the summary and not at the far edge. */
  .toggle {
    display: flex;
    align-items: center;
    gap: 7px;
    max-inline-size: 100%;
    padding-block: 3px;
    color: var(--color-ink-3);
    font-size: var(--text-caption);
    text-align: start;
    transition: color 150ms;
  }

  .toggle:hover {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .toggle:hover {
    color: var(--color-gray-300);
  }

  .toggle:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .lead {
    display: inline-flex;
    flex-shrink: 0;
  }

  .toggle[data-state='done'] .lead {
    color: var(--color-ink-3);
  }

  .toggle[data-state='failed'] .lead {
    color: var(--color-red-500);
  }

  .text {
    display: flex;
    flex: 0 1 auto;
    gap: 6px;
    min-inline-size: 0;
    overflow: hidden;
    white-space: nowrap;
  }

  .label {
    color: var(--color-ink-2);
    font-family: var(--font-mono);
    font-size: 11.5px;
  }

  /* While a call runs the label shimmers (chat-messages look §5.5). */
  .label[data-running] {
    background: linear-gradient(
        110deg,
        var(--color-gray-400) 43%,
        var(--color-gray-200) 50%,
        var(--color-gray-400) 57%
      )
      100% 0 / 200% 100%;
    background-clip: text;
    color: transparent;
    animation: shimmer 1.5s cubic-bezier(0.7, 0, 1, 0.4) infinite;
  }

  .summary {
    overflow: hidden;
    color: var(--color-ink-3);
    text-overflow: ellipsis;
  }

  .caret {
    display: inline-flex;
    color: var(--color-ink-3);
  }

  .calls {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-block: var(--spacing-1);
    padding-inline-start: 22px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .call {
    display: flex;
    gap: 6px;
    min-inline-size: 0;
    white-space: nowrap;
  }

  .call-name {
    font-family: var(--font-mono);
  }

  .call-input,
  .call-output {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  @keyframes shimmer {
    to {
      background-position: -100% 0;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .label[data-running] {
      animation: none;
    }
  }
</style>
