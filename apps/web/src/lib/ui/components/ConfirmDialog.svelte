<script lang="ts">
  // The confirm dialog (workspace look §0.7): a question, a sentence, Cancel and Confirm. It sits
  // above everything, dialogs included.
  import { AlertDialog } from 'bits-ui';

  type Props = {
    open: boolean;
    title?: string;
    message?: string;
    onconfirm: () => void;
    oncancel: () => void;
  };

  let {
    open,
    title = 'Are you sure?',
    message = 'This action cannot be undone. Do you wish to continue?',
    onconfirm,
    oncancel,
  }: Props = $props();
</script>

<AlertDialog.Root {open} onOpenChange={(next) => !next && oncancel()}>
  <AlertDialog.Portal>
    <AlertDialog.Overlay class="confirm-backdrop" />
    <AlertDialog.Content class="confirm-card">
      <AlertDialog.Title class="confirm-title">{title}</AlertDialog.Title>
      <AlertDialog.Description class="confirm-body">{message}</AlertDialog.Description>
      <div class="buttons">
        <AlertDialog.Cancel class="confirm-cancel">Cancel</AlertDialog.Cancel>
        <AlertDialog.Action class="confirm-ok" onclick={onconfirm}>Confirm</AlertDialog.Action>
      </div>
    </AlertDialog.Content>
  </AlertDialog.Portal>
</AlertDialog.Root>

<style>
  :global(.confirm-backdrop) {
    position: fixed;
    inset: 0;
    z-index: 99999999;
    background-color: rgb(0 0 0 / 0.6);
  }

  :global(.confirm-card) {
    position: fixed;
    inset-block-start: 50%;
    inset-inline-start: 50%;
    z-index: 99999999;
    inline-size: min(512px, calc(100vw - 16px));
    padding: 20px;
    border: 1px solid var(--color-white);
    border-radius: 24px;
    background-color: var(--color-white);
    translate: -50% -50%;
  }

  :global([data-theme='dark'] .confirm-card) {
    border-color: var(--color-gray-900);
    background-color: var(--color-gray-950);
  }

  :global(.confirm-title) {
    margin-block-end: 10px;
    font-size: 16px;
    font-weight: var(--font-weight-medium);
    line-height: 24px;
  }

  :global([data-theme='dark'] .confirm-title) {
    color: var(--color-gray-200);
  }

  :global(.confirm-body) {
    color: var(--color-gray-500);
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .buttons {
    display: flex;
    gap: 6px;
    margin-block-start: 20px;
  }

  :global(:is(.confirm-cancel, .confirm-ok)) {
    flex: 1;
    padding-block: 6px;
    border-radius: var(--radius-pill);
    font-size: var(--text-ui);
    transition: background-color 150ms;
  }

  :global(.confirm-cancel) {
    background-color: var(--color-gray-100);
    color: var(--color-gray-800);
  }

  :global(.confirm-cancel:hover) {
    background-color: color-mix(in srgb, var(--color-gray-100) 70%, transparent);
  }

  :global(.confirm-ok) {
    background-color: var(--color-gray-900);
    color: var(--color-gray-100);
  }

  :global(.confirm-ok:hover) {
    background-color: color-mix(in srgb, var(--color-gray-900) 90%, transparent);
  }

  :global([data-theme='dark'] .confirm-cancel) {
    background-color: var(--color-gray-850);
    color: var(--color-white);
  }

  :global([data-theme='dark'] .confirm-cancel:hover) {
    background-color: color-mix(in srgb, var(--color-gray-850) 60%, transparent);
  }

  :global([data-theme='dark'] .confirm-ok) {
    background-color: var(--color-gray-100);
    color: var(--color-gray-800);
  }

  :global([data-theme='dark'] .confirm-ok:hover) {
    background-color: color-mix(in srgb, var(--color-gray-100) 90%, transparent);
  }
</style>
