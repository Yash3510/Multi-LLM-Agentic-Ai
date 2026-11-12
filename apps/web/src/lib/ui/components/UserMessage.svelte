<script lang="ts">
  // A message from the person (chat-messages look §2, bubble layout): the text in a soft bubble
  // at the end of the row, then the time and the edit, copy and delete actions on hover.
  import { m } from '$lib/i18n/generated/messages.js';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { toIntlLocale } from '$lib/ui/format';
  import { writeClipboard } from './clipboard';
  import './message.css';

  type Props = { text: string; at: Date };

  let { text, at }: Props = $props();

  const short = new Intl.DateTimeFormat(toIntlLocale(getLocale()), {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
</script>

<div data-message-row>
  <div class="bubble-row"><div class="bubble">{text}</div></div>
  <div class="actions" data-message-actions>
    <time data-message-time datetime={at.toISOString()}>{short.format(at)}</time>
    <button
      type="button"
      data-message-action
      aria-label={m.message_edit()}
      title={m.message_edit()}
    >
      <Icon name="rename" size={16} />
    </button>
    <button
      type="button"
      data-message-action
      aria-label={m.message_copy()}
      title={m.message_copy()}
      onclick={() => writeClipboard(text)}
    >
      <Icon name="copy" size={16} />
    </button>
    <button
      type="button"
      data-message-action
      aria-label={m.message_delete()}
      title={m.message_delete()}
    >
      <Icon name="trash" size={16} />
    </button>
  </div>
</div>

<style>
  .bubble-row {
    display: flex;
    justify-content: flex-end;
    padding-block-end: var(--spacing-1);
  }

  .bubble {
    max-inline-size: 90%;
    padding: 6px var(--spacing-4);
    border-radius: 20px;
    background-color: var(--color-gray-50);
    color: var(--color-ink-1);
    /* The same size and weight as the reply, so a sent message reads as plain text. */
    font-size: var(--text-body);
    line-height: var(--text-body--line-height);
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }

  :global([data-theme='dark']) .bubble {
    background-color: var(--color-gray-850);
  }

  .actions {
    justify-content: flex-end;
  }
</style>
