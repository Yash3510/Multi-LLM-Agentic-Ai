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
  };

  let { model, text, at, last = false }: Props = $props();

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
      <div class="body" {@attach safeHtml(html)}></div>
      <div class="bar" data-message-actions>
        {#each [{ name: 'rename', label: m.message_edit() }, { name: 'copy', label: m.message_copy() }, { name: 'read-aloud', label: m.message_read_aloud() }, { name: 'thumbs-up', label: m.message_good() }, { name: 'thumbs-down', label: m.message_bad() }, { name: 'regenerate', label: m.message_regenerate() }] as const as action (action.name)}
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
    line-height: 24px;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-white);
  }

  .body {
    color: var(--color-ink-1);
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
