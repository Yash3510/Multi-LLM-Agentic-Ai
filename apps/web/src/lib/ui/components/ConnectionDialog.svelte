<script lang="ts" module>
  export interface Connection {
    url: string;
    /** Kept only in the admin config; never logged. */
    key: string;
    enabled: boolean;
  }
</script>

<script lang="ts">
  // Add or edit a model server connection (admin look §22a): its address, which must be on this
  // machine or a private network, and an optional key. Delete when editing.
  import { Dialog } from 'bits-ui';
  import { isLocalUrl } from '$lib/ui/local-url';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import SecretInput from './SecretInput.svelte';
  import './admin-dialog.css';
  import './modal.css';

  type Props = {
    open: boolean;
    connection?: Connection;
    onsave: (connection: Connection) => void;
    ondelete: () => void;
    onclose: () => void;
  };

  let { open, connection, onsave, ondelete, onclose }: Props = $props();

  let url = $state('');
  let key = $state('');
  let problem = $state('');

  $effect(() => {
    if (!open) return;
    url = connection?.url ?? '';
    key = connection?.key ?? '';
    problem = '';
  });

  function submit(event: SubmitEvent) {
    event.preventDefault();
    const trimmed = url.trim();
    if (!isLocalUrl(trimmed)) {
      problem =
        'Connections are allowed only on this machine or a private network (for example http://localhost:1234/v1).';
      return;
    }
    onsave({ url: trimmed.replace(/\/+$/, ''), key, enabled: connection?.enabled ?? true });
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog small">
        <div class="head connection-head">
          <Dialog.Title>
            {#snippet child({ props })}
              <h3 {...props} class="connection-title">
                {connection ? 'Edit Connection' : 'Add Connection'}
              </h3>
            {/snippet}
          </Dialog.Title>
          <Dialog.Close class="close" aria-label="Close"><Icon name="x" size={20} /></Dialog.Close>
        </div>
        <form class="body" onsubmit={submit}>
          <label>
            <span class="label">URL</span>
            <input class="plain" bind:value={url} placeholder="API Base URL" aria-label="URL" />
          </label>
          <div class="gap">
            <span class="label">Key</span>
            <SecretInput bind:value={key} label="Key" placeholder="API Key" />
          </div>
          {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
          <div class="actions">
            {#if connection}
              <button type="button" class="delete" onclick={ondelete}>Delete</button>
            {:else}
              <span></span>
            {/if}
            <button type="submit" class="pill">Save</button>
          </div>
        </form>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .connection-head {
    padding: 16px 20px 6px;
  }

  .connection-title {
    font-size: 18px;
    font-weight: var(--font-weight-medium);
  }

  .body {
    padding: 0 20px 16px;
  }

  label,
  .gap {
    display: block;
    margin-block-start: 8px;
  }

  label {
    margin-block-start: 6px;
  }

  .actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-block-start: 12px;
  }

  .delete {
    padding: 4px 6px;
    color: var(--color-gray-500);
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
  }

  .delete:hover {
    color: var(--color-gray-700);
    text-decoration: underline;
  }
</style>
