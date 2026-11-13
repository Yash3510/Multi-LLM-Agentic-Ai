<script lang="ts">
  // Set your status (layout look §7.2, F133 to F136): a message and Save; clear empties it. The
  // emoji picker is left for a later piece (it needs emoji data).
  import { Dialog } from 'bits-ui';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './modal.css';

  type Props = {
    open: boolean;
    message?: string;
    onsave: (message: string) => Promise<void>;
    onclose: () => void;
  };

  let { open, message = '', onsave, onclose }: Props = $props();

  let text = $state('');

  $effect(() => {
    if (open) text = message;
  });
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <form
        class="card"
        onsubmit={async (event) => {
          event.preventDefault();
          await onsave(text.trim());
        }}
      >
        <div class="head">
          <Dialog.Title class="status-title">Set your status</Dialog.Title>
          <Dialog.Close class="status-close" aria-label="Close"
            ><Icon name="x" size={16} /></Dialog.Close
          >
        </div>
        <div class="body">
          <span class="label">Status</span>
          <div class="field">
            <input bind:value={text} placeholder="What's on your mind?" aria-label="Status" />
            {#if text}
              <button
                type="button"
                class="clear"
                aria-label="Clear status"
                onclick={() => (text = '')}><Icon name="x" size={16} /></button
              >
            {/if}
          </div>
        </div>
        <div class="footer"><button type="submit" class="save">Save</button></div>
      </form>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
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
    color: var(--color-gray-100);
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 16px 8px;
  }

  :global(.status-title) {
    font-size: 16px;
    line-height: 24px;
  }

  :global(.status-close) {
    display: grid;
  }

  .body {
    padding: 0 16px 16px;
  }

  .label {
    display: block;
    margin-block-end: 6px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .field {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 10px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 12px;
  }

  :global([data-theme='dark']) .field {
    border-color: color-mix(in srgb, var(--color-gray-850) 50%, transparent);
  }

  input {
    flex: 1;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
  }

  input:focus {
    outline: none;
  }

  input::placeholder {
    color: var(--color-gray-500);
  }

  .clear {
    display: grid;
  }

  .footer {
    display: flex;
    justify-content: flex-end;
    padding: 0 16px 16px;
  }

  .save {
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-ui);
  }

  :global([data-theme='dark']) .save {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :global(.status-close:focus-visible),
  :is(.clear, .save):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
