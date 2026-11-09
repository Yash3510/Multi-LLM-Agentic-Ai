<script lang="ts">
  // A tool's settings (workspace look §8.4, F12). The stand-in tools declare none yet, so it shows
  // the empty state until the API supplies them.
  import { Dialog } from 'bits-ui';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './modal.css';

  type Props = { open: boolean; onclose: () => void };

  let { open, onclose }: Props = $props();
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="card">
        <div class="head">
          <Dialog.Title class="settings-title">Settings</Dialog.Title>
          <Dialog.Close class="settings-close" aria-label="Close"
            ><Icon name="x" size={16} /></Dialog.Close
          >
        </div>
        <div class="body"><p class="none">No settings</p></div>
        <div class="footer">
          <button type="button" class="save" onclick={onclose}>Save</button>
        </div>
      </div>
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
    padding: 12px 16px 4px;
  }

  :global(.settings-title) {
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
    line-height: 20px;
  }

  :global(.settings-close) {
    display: grid;
    padding: 4px;
    border-radius: 8px;
    color: var(--color-gray-500);
    transition:
      background-color 150ms,
      color 150ms;
  }

  :global(.settings-close:hover) {
    background-color: var(--color-gray-50);
    color: var(--color-gray-700);
  }

  .body {
    padding: 0 16px 12px;
  }

  .none {
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .footer {
    display: flex;
    justify-content: flex-end;
    padding: 10px 16px 16px;
  }

  .save {
    padding: 6px 12px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-ui);
    line-height: 20px;
    transition: background-color 150ms;
  }

  .save:hover {
    background-color: var(--color-gray-950);
  }

  :global([data-theme='dark']) .save {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :global(.settings-close:focus-visible),
  .save:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
