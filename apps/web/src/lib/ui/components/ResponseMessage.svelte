<script lang="ts">
  // An answer (chat-messages look §3.1, §3.4, §3.6): the 4CE mark in a 40 px slot, the agent's
  // name, the body in 15 px prose (markdown, sanitised), and the action bar.
  import { m } from '$lib/i18n/generated/messages.js';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { toIntlLocale } from '$lib/ui/format';
  import { renderMarkdown, safeHtml } from '$lib/ui/markdown';
  import { writeClipboard } from './clipboard';
  import Logomark from './Logomark.svelte';
  import StageRail from './StageRail.svelte';
  import StatusLine from './StatusLine.svelte';
  import SourcesBar from './SourcesBar.svelte';
  import ToolGroup from './ToolGroup.svelte';
  import ReceiptStrip from './ReceiptStrip.svelte';
  import RunErrorCard from './RunErrorCard.svelte';
  import { deriveRun, RAIL } from '$lib/data/stages';
  import type { StreamEvent } from '$lib/data';
  import type { RailStage } from '$lib/data/stages';
  import './message.css';

  type Props = {
    model: string;
    text: string;
    at: Date;
    /** The last answer keeps its actions shown. */
    last?: boolean;
    /** The status line under the name (own-4ce look S5), e.g. "Answered directly". */
    status?: string;
    /** A direct reply's receipt line: the model that answered and how long it took. */
    direct?: { model: string; seconds: number };
    /** The run's events, for the stage rail. */
    events?: StreamEvent[];
    finished?: boolean;
    /** Offered on the last answer: run it again after it stopped with an error. */
    onretry?: () => void;
  };

  let {
    model,
    text,
    at,
    last = false,
    status,
    direct,
    events,
    finished = true,
    onretry,
  }: Props = $props();

  const ACTIONS = [
    { name: 'rename', label: m.message_edit() },
    { name: 'copy', label: m.message_copy() },
    { name: 'read-aloud', label: m.message_read_aloud() },
    { name: 'info', label: m.message_info() },
    { name: 'thumbs-up', label: m.message_good() },
    { name: 'thumbs-down', label: m.message_bad() },
    { name: 'continue', label: m.message_continue() },
    { name: 'regenerate', label: m.message_regenerate() },
    { name: 'fork', label: m.message_fork() },
  ] as const;

  // Sources once each, by citation number; tool calls at their latest state.
  const sources = $derived(
    [
      ...new Map(
        (events ?? []).flatMap((event) =>
          event.type === 'source' ? [[event.source.index, event.source] as const] : [],
        ),
      ).values(),
    ].sort((a, b) => a.index - b.index),
  );
  const calls = $derived([
    ...new Map(
      (events ?? []).flatMap((event) =>
        event.type === 'tool' ? [[event.call.id, event.call] as const] : [],
      ),
    ).values(),
  ]);
  const html = $derived(renderMarkdown(text, sources));
  const failure = $derived((events ?? []).findLast((event) => event.type === 'error'));
  // The role the run stopped at names the card; the gate and no rail fall back to 4CE.
  const stoppedAt = $derived.by(() => {
    if (!failure || !events) return undefined;
    const run = deriveRun(events, true, Date.now());
    const stage = RAIL.find((item) => run.stages[item].note === 'failed');
    if (!stage || stage === 'sign-off') return undefined;
    return stage.charAt(0).toUpperCase() + stage.slice(1);
  });
  let handover = $state<RailStage | undefined>();
  const receipt = $derived((events ?? []).findLast((event) => event.type === 'receipt'));
  const decision = $derived((events ?? []).findLast((event) => event.type === 'decision'));
  const checks = $derived(
    (events ?? []).findLast((event) => event.type === 'sign-off')?.request.checks ?? [],
  );
  // Text is still arriving: live, with some text, and not yet handed to the person.
  const typing = $derived(
    !finished && text.length > 0 && !(events ?? []).some((event) => event.type === 'sign-off'),
  );
  const short = new Intl.DateTimeFormat(toIntlLocale(getLocale()), {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
</script>

<div data-message-row data-actions-shown={last ? '' : undefined}>
  <div class="response">
    <div class="avatar"><Logomark size={30} /></div>
    <div class="column">
      <div class="name">{model}</div>
      {#if events}
        <StageRail {events} {finished} onhandover={(role) => (handover = role)} />
        <StatusLine {events} {finished} {handover} />
        {#if calls.length}<ToolGroup {calls} />{/if}
      {/if}
      {#if status}<div class="status">{status}</div>{/if}
      {#if failure}
        <RunErrorCard
          detail={failure.message}
          advice={failure.advice}
          role={stoppedAt}
          onretry={last ? onretry : undefined}
        />
      {:else}
        <div class="body" data-typing={typing ? '' : undefined} {@attach safeHtml(html)}></div>
      {/if}
      {#if sources.length}<SourcesBar {sources} />{/if}
      {#if receipt && decision?.outcome === 'released'}
        <ReceiptStrip receipt={receipt.receipt} {checks} releasedAt={new Date(decision.at)} />
      {/if}
      {#if direct}
        <p class="direct">
          {m.message_direct_reply()} · <code>{direct.model}</code> · {direct.seconds.toFixed(1)}s — {m.message_direct_reason()}
        </p>
      {/if}
      {#if finished}
        <div class="bar" data-message-actions>
          {#each ACTIONS as action (action.name)}
            <button
              type="button"
              data-message-action
              aria-label={action.label}
              title={action.label}
              onclick={action.name === 'copy' ? () => writeClipboard(text) : undefined}
            >
              <Icon name={action.name} size={16} />
            </button>
          {/each}
          <time data-message-time datetime={at.toISOString()}>{short.format(at)}</time>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .response {
    display: flex;
    inline-size: 100%;
  }

  .avatar {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 40px;
    block-size: 40px;
    margin-block-start: -9px;
    margin-inline-end: 10px;
  }

  .column {
    flex: auto;
    inline-size: 0;
    padding-inline-start: var(--spacing-1);
  }

  .name {
    color: var(--color-black);
    font-size: var(--text-body);
    line-height: 1.5;
  }

  /* Gaps measured on the running app: 2 px under the name, 10 px before the body. */
  .status {
    margin-block: 2px 10px;
    color: var(--color-gray-600);
    font-size: var(--text-body);
    line-height: 1.5;
  }

  :global([data-theme='dark']) .status {
    color: var(--color-gray-400);
  }

  /* The direct-reply receipt line (own-4ce look): italic prose with the model in a mono chip. */
  .direct {
    margin-block-start: 12px;
    color: var(--color-prose);
    font-size: var(--text-body);
    font-style: italic;
    line-height: 1.625;
  }

  .direct code {
    padding: 2.4px 4.8px;
    border-radius: 6px;
    background-color: var(--color-gray-100);
    color: var(--color-gray-800);
    font-family: var(--font-mono);
    font-size: 0.85em;
    font-style: normal;
  }

  :global([data-theme='dark']) .direct code {
    background-color: var(--color-gray-800);
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .name {
    color: var(--color-white);
  }

  .body {
    color: var(--color-prose);
    font-size: var(--text-body);
    /* The answer prose's relaxed line (24.4 px at 15 px), measured on the running app. */
    line-height: 1.625;
    overflow-wrap: anywhere;
  }

  /* Answer prose (chat-messages look §5): 4 px paragraph margins, compact lists, quiet tables
     and code on the code ground. */
  .body :global(:is(p, ul, ol, table, pre, blockquote)) {
    margin-block: var(--spacing-1);
  }

  .body :global(:is(ul, ol)) {
    padding-inline-start: 1.5em;
  }

  .body :global(ul) {
    list-style: disc;
  }

  .body :global(ol) {
    list-style: decimal;
  }

  .body :global(li) {
    margin-block: 2px;
  }

  .body :global(a) {
    text-decoration: underline;
    text-underline-offset: 2px;
  }

  .body :global(strong) {
    font-weight: var(--font-weight-semibold);
  }

  .body :global(table) {
    border-collapse: collapse;
    font-size: var(--text-small);
  }

  .body :global(:is(th, td)) {
    padding: var(--spacing-1) var(--spacing-3);
    border-block-end: 1px solid var(--color-line-1);
  }

  /* Columns marked right-aligned in the markdown (numbers) keep their align attribute. */
  .body :global(:is(th, td):not([align])) {
    text-align: start;
  }

  .body :global(th) {
    font-weight: var(--font-weight-medium);
  }

  .body :global(pre) {
    padding: var(--spacing-3);
    overflow-x: auto;
    border-radius: var(--radius-inset);
    background-color: var(--color-code-ground);
    color: var(--color-code-ink);
    font-size: var(--text-small);
  }

  /* Evidence chips for [n] (own-4ce look S14). */
  .body :global(cite) {
    display: inline-flex;
    align-items: center;
    max-inline-size: 16rem;
    margin-inline: 1px;
    padding: 1px 6px;
    overflow: hidden;
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-50);
    color: var(--color-gray-700);
    font-size: 0.66rem;
    font-style: normal;
    font-weight: var(--font-weight-medium);
    line-height: 1.35;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: baseline;
    translate: 0 1px;
    cursor: pointer;
  }

  .body :global(cite:hover) {
    border-color: var(--color-gray-300);
    background-color: var(--color-gray-100);
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .body :global(cite) {
    border-color: var(--color-gray-700);
    background-color: var(--color-gray-850);
    color: var(--color-gray-200);
  }

  .body :global(:not(pre) > code) {
    padding: 1px 4px;
    border-radius: var(--radius-tight);
    background-color: var(--color-gray-50);
    font-size: 0.9em;
  }

  /* The typing caret at the end of the text while it streams (chat-messages look §3.4). */
  .body[data-typing] > :global(:last-child)::after {
    content: '';
    display: inline-block;
    inline-size: 2px;
    block-size: 14px;
    margin-inline-start: 2px;
    background-color: var(--color-gray-400);
    vertical-align: baseline;
    animation: pulse 1s ease-in-out infinite;
  }

  :global([data-theme='dark']) .body[data-typing] > :global(:last-child)::after {
    background-color: var(--color-gray-500);
  }

  @keyframes pulse {
    50% {
      opacity: 0.3;
    }
  }

  .bar {
    margin-block-start: 2px;
    margin-inline-start: -6px;
    overflow-x: auto;
    scrollbar-width: none;
  }
</style>
