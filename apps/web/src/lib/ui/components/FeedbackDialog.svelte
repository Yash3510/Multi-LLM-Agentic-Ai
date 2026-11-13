<script lang="ts">
  // One rating's details (admin look §14a, F129 to F132): the chat, the prompt and response, the
  // detailed rating, reason, comment and tags.
  import { Dialog } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { Feedback } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './admin-dialog.css';
  import './modal.css';

  type Props = { open: boolean; feedback?: Feedback; onclose: () => void };

  let { open, feedback, onclose }: Props = $props();
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog small">
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}<h3 {...props} class="title">Feedback Details</h3>{/snippet}
          </Dialog.Title>
          <Dialog.Close class="close" aria-label="Close"><Icon name="x" size={16} /></Dialog.Close>
        </div>
        {#if feedback}
          <div class="body">
            <div class="field">
              <span class="label">Chat ID</span>
              {#if feedback.chatId}
                <a
                  class="value link"
                  href={resolve('/c/[id]', { id: feedback.chatId })}
                  target="_blank"
                  rel="noopener">{feedback.chatId}</a
                >
              {:else}<span class="value">-</span>{/if}
            </div>
            {#if feedback.prompt}
              <div class="field">
                <span class="label">Prompt</span>
                <p class="value pre">{feedback.prompt}</p>
              </div>
            {/if}
            {#if feedback.response}
              <div class="field">
                <span class="label">Response</span>
                <p class="value pre scroll">{feedback.response}</p>
              </div>
            {/if}
            {#each [['Rating', feedback.rating], ['Reason', feedback.reason], ['Comment', feedback.comment]] as [label, value] (label)}
              <div class="field">
                <span class="label">{label}</span><span class="value">{value ?? '-'}</span>
              </div>
            {/each}
            {#if feedback.tags.length}
              <div class="tags">
                {#each feedback.tags as tag (tag)}<span class="tag">{tag}</span>{/each}
              </div>
            {/if}
            <div class="footer">
              <button type="button" class="pill" onclick={onclose}>Close</button>
            </div>
          </div>
        {/if}
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .body {
    padding: 0 16px 16px;
  }

  .field {
    display: flex;
    flex-direction: column;
    margin-block-end: 8px;
  }

  .value {
    font-size: var(--text-caption);
  }

  .link:hover {
    text-decoration: underline;
  }

  .pre {
    overflow-wrap: anywhere;
    white-space: pre-wrap;
  }

  .scroll {
    max-block-size: 128px;
    overflow-y: auto;
  }

  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin: 4px -4px 8px;
  }

  .tag {
    padding: 2px 8px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-100);
    font-size: 0.5625rem;
  }

  :global([data-theme='dark']) .tag {
    background-color: var(--color-gray-850);
  }

  .footer {
    padding-block-start: 8px;
  }
</style>
