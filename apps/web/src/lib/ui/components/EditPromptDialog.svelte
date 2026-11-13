<script lang="ts">
  // Edit prompt (workspace look §6.3, F97): the live text to change, an optional commit message,
  // and whether the new version goes live. Saving adds a version.
  import { Dialog } from 'bits-ui';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './modal.css';

  type Props = {
    open: boolean;
    content: string;
    onsave: (version: { content: string; message?: string; live: boolean }) => Promise<void>;
    onclose: () => void;
  };

  let { open, content, onsave, onclose }: Props = $props();

  let text = $state('');
  let message = $state('');
  let live = $state(true);
  let saving = $state(false);

  // Each opening starts from the live text (F97).
  $effect(() => {
    if (open) {
      text = content;
      message = '';
      live = true;
    }
  });

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    saving = true;
    try {
      await onsave({ content: text, message: message.trim() || undefined, live });
    } finally {
      saving = false;
    }
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <form class="card" novalidate onsubmit={submit}>
        <div class="head">
          <Dialog.Title class="edit-title">Edit Prompt</Dialog.Title>
          <Dialog.Close class="edit-close" aria-label="Close"
            ><Icon name="x" size={16} /></Dialog.Close
          >
        </div>
        <label class="field">
          <span class="caption">Prompt Content</span>
          <textarea bind:value={text} rows="6" aria-label="Prompt Content" required></textarea>
        </label>
        <label class="field">
          <span class="caption">Commit Message (optional)</span>
          <input bind:value={message} placeholder="Describe what changed..." />
        </label>
        <div class="footer">
          <label class="live">
            <input type="checkbox" bind:checked={live} />
            Set as Production
          </label>
          <button type="submit" class="save" disabled={saving}>
            Save
            {#if saving}<span class="spinner" aria-hidden="true"></span>{/if}
          </button>
        </div>
      </form>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .card {
    inline-size: 896px;
    max-inline-size: 100%;
    margin: auto;
    padding: 12px 16px 16px;
    border: 1px solid var(--color-white);
    border-radius: 20px;
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .card {
    border-color: var(--color-gray-850);
    background-color: var(--color-gray-900);
    color: var(--color-gray-100);
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: 8px;
  }

  :global(.edit-title) {
    font-size: var(--text-caption);
    line-height: 16px;
  }

  :global(.edit-close) {
    display: grid;
    padding: 4px;
    border-radius: 8px;
    color: var(--color-gray-500);
    transition:
      background-color 150ms,
      color 150ms;
  }

  :global(.edit-close:hover) {
    background-color: var(--color-gray-50);
    color: var(--color-gray-700);
  }

  .field {
    display: block;
    margin-block: 8px;
  }

  .caption {
    display: block;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  textarea,
  input:not([type='checkbox']) {
    inline-size: 100%;
    margin-block-start: 4px;
    background: transparent;
    color: inherit;
    font-size: var(--text-caption);
    line-height: 16px;
    resize: none;
    field-sizing: content;
  }

  :is(textarea, input):focus {
    outline: none;
  }

  input::placeholder {
    color: var(--color-gray-400);
  }

  .footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-start: 16px;
  }

  .live {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    line-height: 16px;
    cursor: pointer;
  }

  .live input {
    inline-size: 16px;
    block-size: 16px;
  }

  :global([data-theme='dark']) .live {
    color: var(--color-gray-300);
  }

  .save {
    display: flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: background-color 150ms;
  }

  .save:hover {
    background-color: var(--color-gray-900);
  }

  .save:disabled {
    background-color: var(--color-gray-200);
    color: var(--color-gray-500);
    cursor: not-allowed;
  }

  :global([data-theme='dark']) .save {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  .spinner {
    inline-size: 16px;
    block-size: 16px;
    margin-inline-start: 6px;
    border: 2px solid color-mix(in srgb, currentcolor 25%, transparent);
    border-block-start-color: currentcolor;
    border-radius: var(--radius-pill);
    animation: spin 0.75s linear infinite;
  }

  @keyframes spin {
    to {
      rotate: 1turn;
    }
  }

  :global(.edit-close:focus-visible),
  .save:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
