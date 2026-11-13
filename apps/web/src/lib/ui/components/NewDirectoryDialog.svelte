<script lang="ts">
  // New directory (workspace look §5.5, F76): one name, Cancel and Create. Enter creates.
  import { Dialog } from 'bits-ui';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './modal.css';

  type Props = {
    open: boolean;
    oncreate: (name: string) => Promise<void>;
    onclose: () => void;
  };

  let { open, oncreate, onclose }: Props = $props();

  let name = $state('');
  let problem = $state('');

  // The field starts empty each time the dialog opens (F76).
  $effect(() => {
    if (open) {
      name = '';
      problem = '';
    }
  });

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!name.trim()) {
      problem = 'Name is required.';
      return;
    }
    await oncreate(name.trim());
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame">
      <div class="card">
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}<h3 {...props} class="dir-title">New Directory</h3>{/snippet}
          </Dialog.Title>
          <Dialog.Close class="dir-close" aria-label="Close"
            ><Icon name="x" size={16} /></Dialog.Close
          >
        </div>
        <form novalidate onsubmit={submit}>
          <label class="body">
            <span class="caption">Name</span>
            <input bind:value={name} placeholder="Directory name" />
          </label>
          {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
          <div class="footer">
            <button type="button" class="cancel" onclick={onclose}>Cancel</button>
            <button type="submit" class="create">Create</button>
          </div>
        </form>
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

  :global(.dir-title) {
    font-size: 16px;
    font-weight: 400;
    line-height: 24px;
  }

  :global(.dir-close) {
    display: grid;
    margin-inline-start: 8px;
  }

  .body {
    display: block;
    padding: 0 16px 8px;
  }

  .caption {
    display: block;
    margin-block-end: 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  /* The running app sets the field 3 px lower under its caption and 1 px clear of the footer. */
  input {
    display: block;
    inline-size: 100%;
    margin-block: 3px 1px;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  input:focus {
    outline: none;
  }

  input::placeholder {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) input::placeholder {
    color: var(--color-gray-700);
  }

  .problem {
    padding-inline: 16px;
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }

  .footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    padding: 8px 16px 14px;
  }

  .cancel {
    padding: 4px 12px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: color 150ms;
  }

  .cancel:hover {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .cancel:hover {
    color: var(--color-gray-200);
  }

  .create {
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-ui);
    line-height: 20px;
    transition: background-color 150ms;
  }

  .create:hover {
    background-color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .create {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :global([data-theme='dark']) .create:hover {
    background-color: var(--color-gray-100);
  }

  :global(.dir-close:focus-visible),
  :is(.cancel, .create):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
