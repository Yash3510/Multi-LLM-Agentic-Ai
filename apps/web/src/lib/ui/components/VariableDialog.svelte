<script lang="ts">
  // Add or edit a user variable (chat-composer look §9.14): a snake-case key and a value; Delete
  // when editing, Cancel and Done.
  import { Dialog } from 'bits-ui';
  import './modal.css';

  type Props = {
    open: boolean;
    /** The variable to edit; none adds one. */
    variable?: { key: string; value: string };
    /** Keys already taken by other variables. */
    taken: string[];
    ondone: (variable: { key: string; value: string }) => void;
    ondelete: () => void;
    onclose: () => void;
  };

  let { open, variable, taken, ondone, ondelete, onclose }: Props = $props();

  let key = $state('');
  let value = $state('');
  let problem = $state('');

  $effect(() => {
    if (!open) return;
    key = variable?.key ?? '';
    value = variable?.value ?? '';
    problem = '';
  });

  function submit(event: SubmitEvent) {
    event.preventDefault();
    const trimmed = key.trim();
    if (!/^[a-z][a-z0-9_]*$/.test(trimmed)) {
      problem = 'Variable keys must use lowercase snake case.';
      return;
    }
    if (taken.includes(trimmed)) {
      problem = 'Variable keys must be unique.';
      return;
    }
    ondone({ key: trimmed, value });
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <form class="card" onsubmit={submit}>
        <Dialog.Title>
          {#snippet child({ props })}
            <h3 {...props} class="title">
              {variable ? 'Edit User Variable' : 'Add User Variable'}
            </h3>
          {/snippet}
        </Dialog.Title>
        <span class="caption">Key</span>
        <input
          class="field mono"
          bind:value={key}
          aria-label="Variable key"
          placeholder="key_name"
        />
        <span class="caption value-caption">Value</span>
        <textarea
          class="field area"
          bind:value
          aria-label="Variable value"
          placeholder="Value"
          rows="3"></textarea>
        {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
        <div class="footer">
          {#if variable}
            <button type="button" class="quiet" onclick={ondelete}>Delete</button>
          {:else}
            <span></span>
          {/if}
          <span class="end">
            <button type="button" class="quiet" onclick={onclose}>Cancel</button>
            <button type="submit" class="done">Done</button>
          </span>
        </div>
      </form>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .card {
    display: flex;
    flex-direction: column;
    inline-size: 480px;
    max-inline-size: 100%;
    margin: auto;
    padding: 16px;
    border: 1px solid var(--color-white);
    border-radius: 20px;
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .card {
    border-color: var(--color-gray-850);
    background-color: var(--color-gray-900);
    color: var(--color-gray-100);
  }

  .title {
    margin-block-end: 12px;
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
  }

  .caption {
    margin-block-end: 4px;
    color: var(--color-gray-400);
    font-size: 10px;
  }

  .value-caption {
    margin-block-start: 12px;
  }

  :global([data-theme='dark']) .caption {
    color: var(--color-gray-600);
  }

  .field {
    inline-size: 100%;
    padding: 6px 8px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-700);
    font-size: var(--text-caption);
  }

  .field::placeholder {
    color: var(--color-gray-300);
  }

  .field:focus {
    border-color: var(--color-blue-400);
    outline: none;
  }

  :global([data-theme='dark']) .field {
    border-color: rgb(255 255 255 / 0.04);
    background-color: rgb(255 255 255 / 0.03);
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .field::placeholder {
    color: var(--color-gray-700);
  }

  .mono {
    font-family: var(--font-mono);
  }

  .area {
    resize: none;
  }

  .problem {
    margin-block-start: 8px;
    color: var(--color-red-600);
    font-size: var(--text-micro);
  }

  .footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-start: 16px;
  }

  .end {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .quiet {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    transition: color 150ms;
  }

  .quiet:hover {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .quiet:hover {
    color: var(--color-white);
  }

  .done {
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-ui);
  }

  :global([data-theme='dark']) .done {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :is(.quiet, .done):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
