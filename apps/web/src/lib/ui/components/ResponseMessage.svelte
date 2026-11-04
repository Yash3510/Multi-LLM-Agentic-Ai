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
  };

  let { model, text, at, last = false, status, direct }: Props = $props();

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

  const html = $derived(renderMarkdown(text));
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
      {#if status}<div class="status">{status}</div>{/if}
      <div class="body" {@attach safeHtml(html)}></div>
      {#if direct}
        <p class="direct">
          {m.message_direct_reply()} · <code>{direct.model}</code> · {direct.seconds.toFixed(1)}s — {m.message_direct_reason()}
        </p>
      {/if}
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

  .body :global(:not(pre) > code) {
    padding: 1px 4px;
    border-radius: var(--radius-tight);
    background-color: var(--color-gray-50);
    font-size: 0.9em;
  }

  .bar {
    margin-block-start: 2px;
    margin-inline-start: -6px;
    overflow-x: auto;
    scrollbar-width: none;
  }
</style>
