<script lang="ts">
  // The chat top bar (chat-composer look §2.1): the title, the chat-actions button for a saved
  // chat, and the caller's right-hand cluster (temporary chat, egress, controls). Icon buttons are
  // the quiet 18 px kind (ADR-0041 amendment).
  import type { Snippet } from 'svelte';
  import { m } from '$lib/i18n/generated/messages.js';
  import IconButton from './IconButton.svelte';

  type Props = {
    /** The saved chat's title; a new chat shows "New Chat". */
    title?: string;
    onchatactions?: () => void;
    /** Before the title, e.g. the open-sidebar button on phones. */
    start?: Snippet;
    /** The right-hand cluster. */
    end?: Snippet;
  };

  let { title, onchatactions, start, end }: Props = $props();
</script>

<div class="bar">
  {@render start?.()}
  <div class="title">
    <span class="truncate">{title ?? m.shell_new_chat()}</span>
    {#if title && onchatactions}
      <IconButton icon="dots-three" label={m.shell_chat_actions()} onclick={onchatactions} />
    {/if}
  </div>
  {#if end}
    <div class="end">{@render end()}</div>
  {/if}
</div>

<style>
  .bar {
    position: sticky;
    inset-block-start: 0;
    z-index: 30;
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
    padding: 2px var(--spacing-1) var(--spacing-1) 6px;
    /* A soft fade so content scrolls away under the bar. */
    background: linear-gradient(
      to bottom,
      var(--color-surface-page),
      color-mix(in srgb, var(--color-surface-page) 95%, transparent) 50%,
      transparent
    );
  }

  .title {
    display: flex;
    flex: 1;
    align-items: center;
    gap: var(--spacing-2);
    min-inline-size: 0;
    padding: 2px var(--spacing-1);
    color: var(--color-ink-2);
    font-size: var(--text-body);
  }

  .end {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: var(--spacing-2);
  }
</style>
