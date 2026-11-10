<script lang="ts">
  // Add or edit a memory (chat-composer look §9.9): its type (User or Context), the text and an
  // optional path; Add or Update saves it.
  import { Dialog } from 'bits-ui';
  import type { Memory, MemoryDraft } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './modal.css';

  type Props = {
    open: boolean;
    /** The memory to edit; none adds one. */
    memory?: Memory;
    onsave: (draft: MemoryDraft) => Promise<void>;
    onclose: () => void;
  };

  let { open, memory, onsave, onclose }: Props = $props();

  let type = $state<MemoryDraft['type']>('user');
  let content = $state('');
  let path = $state('');
  let saving = $state(false);

  $effect(() => {
    if (!open) return;
    type = memory?.type ?? 'user';
    content = memory?.content ?? '';
    path = memory?.path ?? '';
  });

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!content.trim() || saving) return;
    saving = true;
    try {
      await onsave({ content: content.trim(), type, path: path.trim() || undefined });
    } finally {
      saving = false;
    }
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <form class="card" onsubmit={submit}>
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}
              <h3 {...props} class="title">{memory ? 'Edit Memory' : 'Add Memory'}</h3>
            {/snippet}
          </Dialog.Title>
          <Dialog.Close class="memory-close" aria-label="Close"
            ><Icon name="x" size={20} /></Dialog.Close
          >
        </div>
        <div class="body">
          <div class="type">
            <span class="label">Type</span>
            <button
              type="button"
              class="toggle"
              onclick={() => (type = type === 'user' ? 'context' : 'user')}
              >{type === 'user' ? 'User' : 'Context'}</button
            >
          </div>
          <textarea
            bind:value={content}
            rows="6"
            aria-label="Memory"
            placeholder={type === 'user'
              ? 'Add a preference, fact, or instruction about you'
              : 'Add durable context for future chats'}></textarea>
          <label class="path">
            <span class="label">Path <span class="optional">(optional)</span></span>
            <input bind:value={path} placeholder="Path" />
          </label>
          <div class="footer">
            <button type="submit" class="save" disabled={saving}>{memory ? 'Update' : 'Add'}</button
            >
          </div>
        </div>
      </form>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  /* The small dialog shell (common look F1). */
  .card {
    inline-size: 480px;
    max-inline-size: 100%;
    margin: auto;
    border: 1px solid var(--color-white);
    border-radius: 20px;
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .card {
    border-color: var(--color-gray-850);
    background-color: var(--color-gray-900);
    color: var(--color-gray-200);
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px 8px;
  }

  :global([data-theme='dark']) .head {
    color: var(--color-gray-300);
  }

  .title {
    font-size: 18px;
    font-weight: var(--font-weight-medium);
    line-height: 28px;
  }

  :global(.memory-close) {
    display: grid;
  }

  .body {
    display: flex;
    flex-direction: column;
    padding: 0 20px 16px;
  }

  .type {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: 6px;
  }

  .label {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .optional {
    opacity: 0.5;
  }

  .toggle {
    color: var(--color-gray-700);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .toggle {
    color: var(--color-gray-300);
  }

  textarea,
  input {
    inline-size: 100%;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
  }

  textarea {
    resize: vertical;
  }

  :is(textarea, input):focus {
    outline: none;
  }

  :is(textarea, input)::placeholder {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) :is(textarea, input)::placeholder {
    color: var(--color-gray-700);
  }

  .path {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-block-start: 8px;
  }

  .footer {
    display: flex;
    justify-content: flex-end;
    padding-block-start: 4px;
  }

  .save {
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
  }

  .save:disabled {
    opacity: 0.6;
  }

  :global([data-theme='dark']) .save {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :global(.memory-close:focus-visible),
  :is(.toggle, .save):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
