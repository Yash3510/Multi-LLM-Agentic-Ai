<script lang="ts">
  // An answer (chat-messages look §3.1, §3.4, §3.6): the 4CE mark in a 40 px slot, the agent's
  // name, the body in 15 px prose, and the action bar. Paragraphs are split on blank lines until
  // the content renderer (markdown, citations) lands.
  import { m } from '$lib/i18n/generated/messages.js';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { toIntlLocale } from '$lib/ui/format';
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

  const paragraphs = $derived(text.split(/\n{2,}/).filter((part) => part.trim()));
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
      <div class="body">
        {#each paragraphs as paragraph, index (index)}
          <p>{paragraph}</p>
        {/each}
      </div>
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
    line-height: 1.75;
    overflow-wrap: anywhere;
  }

  .body p {
    margin-block: var(--spacing-1);
  }

  .bar {
    margin-block-start: 2px;
    margin-inline-start: -6px;
    overflow-x: auto;
    scrollbar-width: none;
  }
</style>
