<script lang="ts">
  // Image size limit (chat-composer look §9.16, F93): the largest width and height an uploaded
  // image keeps when compression is on.
  import { Dialog } from 'bits-ui';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './modal.css';

  type Size = { width: string; height: string };
  type Props = {
    open: boolean;
    size?: Size;
    onsave: (size: Size) => void;
    onclose: () => void;
  };

  let { open, size, onsave, onclose }: Props = $props();

  let width = $state('');
  let height = $state('');

  $effect(() => {
    if (!open) return;
    width = size?.width ?? '';
    height = size?.height ?? '';
  });
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="card">
        <div class="head">
          <Dialog.Title class="manage-title">Manage</Dialog.Title>
          <Dialog.Close class="manage-close" aria-label="Close modal"
            ><Icon name="x" size={16} /></Dialog.Close
          >
        </div>
        <div class="body">
          <p class="caption">Image Max Compression Size</p>
          <div class="sizes">
            <input
              bind:value={width}
              type="number"
              min="0"
              placeholder="Width"
              aria-label="Width"
            />
            <Icon name="x" size={12} />
            <input
              bind:value={height}
              type="number"
              min="0"
              placeholder="Height"
              aria-label="Height"
            />
          </div>
        </div>
        <div class="footer">
          <button type="button" class="save" onclick={() => onsave({ width, height })}>Save</button>
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
    border-radius: 32px;
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .card {
    border-color: var(--color-gray-850);
    background-color: var(--color-gray-900);
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 16px 8px;
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .head {
    color: var(--color-white);
  }

  :global(.manage-title) {
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
  }

  :global(.manage-close) {
    display: grid;
  }

  .body {
    padding: 0 16px 16px;
    color: var(--color-gray-600);
  }

  .caption {
    margin-block-end: 8px;
    font-size: var(--text-caption);
  }

  .sizes {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px;
    color: var(--color-gray-500);
  }

  input {
    flex: 1;
    block-size: 28px;
    padding-inline: 8px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    text-align: center;
  }

  input:focus {
    border-color: var(--color-blue-400);
    outline: none;
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

  :global(.manage-close:focus-visible),
  .save:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
