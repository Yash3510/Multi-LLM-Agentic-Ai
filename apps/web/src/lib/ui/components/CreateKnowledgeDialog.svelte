<script lang="ts">
  // Create a knowledge base (workspace look §4.4, F65): a name, what it is for, and who can use
  // it. A missing field is said once and nothing typed is lost.
  import { Dialog } from 'bits-ui';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import AccessPanel from './AccessPanel.svelte';

  type Props = {
    open: boolean;
    oncreate: (name: string, description: string) => Promise<void>;
    onclose: () => void;
  };

  let { open, oncreate, onclose }: Props = $props();

  let name = $state('');
  let description = $state('');
  let problem = $state('');
  let saving = $state(false);

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!name.trim() || !description.trim()) {
      problem = 'Please fill in all fields.';
      return;
    }
    problem = '';
    saving = true;
    try {
      await oncreate(name.trim(), description.trim());
    } catch (error) {
      problem = error instanceof Error ? error.message : String(error);
    } finally {
      saving = false;
    }
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame">
      <div class="modal-card">
        <div class="title-row">
          <Dialog.Title level={3} class="modal-title">Create a knowledge base</Dialog.Title>
          <Dialog.Close class="modal-close" aria-label="Close"
            ><Icon name="x" size={20} /></Dialog.Close
          >
        </div>
        <form novalidate onsubmit={submit}>
          <div class="fields">
            <label>
              <span class="caption">What are you working on?</span>
              <span class="control">
                <input bind:value={name} placeholder="Name your knowledge base" required />
              </span>
            </label>
            <label>
              <span class="caption">What are you trying to achieve?</span>
              <textarea
                bind:value={description}
                rows="6"
                placeholder="Describe your knowledge base and objectives"
                required></textarea>
            </label>
          </div>
          <div class="access"><AccessPanel /></div>
          {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
          <div class="footer">
            <button type="button" class="cancel" onclick={onclose}>Cancel</button>
            <button type="submit" class="create" disabled={saving}>
              Create Knowledge
              {#if saving}<span class="spinner" aria-hidden="true"></span>{/if}
            </button>
          </div>
        </form>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  :global(.modal-backdrop) {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background-color: rgb(0 0 0 / 0.45);
  }

  :global([data-theme='dark'] .modal-backdrop) {
    background-color: rgb(0 0 0 / 0.6);
  }

  /* The modal (look §0.7) centres its card in a scrolling frame whose 7.2 px scrollbar gutter
     sets the card half a gutter left of the window's centre; the right padding keeps that room. */
  :global(.modal-frame) {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    padding: 12px calc(12px + 0.45rem) 12px 12px;
    overflow-y: auto;
  }

  .modal-card {
    inline-size: 672px;
    max-inline-size: 100%;
    margin: auto;
    border: 1px solid var(--color-white);
    border-radius: 20px;
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .modal-card {
    border-color: var(--color-gray-850);
    background-color: var(--color-gray-900);
    color: var(--color-gray-100);
  }

  .title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px 8px;
  }

  :global(.modal-title) {
    font-size: 16px;
    font-weight: 400;
    line-height: 24px;
  }

  :global(.modal-close) {
    display: grid;
    flex-shrink: 0;
    margin-inline-start: 8px;
  }

  :global(.modal-close:focus-visible) {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }

  form {
    padding: 0 20px 12px;
  }

  .fields {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  label {
    display: block;
  }

  .caption {
    display: block;
    margin-block-end: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  /* The running app's input sits 11 px under its caption and 11 px above the next one. */
  .control {
    display: block;
    padding-block: 3px 1px;
  }

  input,
  textarea {
    inline-size: 100%;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    line-height: 20px;
    resize: none;
  }

  :is(input, textarea):focus {
    outline: none;
  }

  :is(input, textarea)::placeholder {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) :is(input, textarea)::placeholder {
    color: var(--color-gray-700);
  }

  /* 8 px in the look, 9 px as the running app measures (its select sits 20 px under the text). */
  .access {
    margin-block-start: 9px;
  }

  .problem {
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }

  .footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding-block-start: 12px;
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
    display: flex;
    align-items: center;
    gap: 6px;
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

  .create:disabled {
    cursor: not-allowed;
  }

  :global([data-theme='dark']) .create {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :global([data-theme='dark']) .create:hover {
    background-color: var(--color-gray-100);
  }

  .spinner {
    inline-size: 16px;
    block-size: 16px;
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
</style>
