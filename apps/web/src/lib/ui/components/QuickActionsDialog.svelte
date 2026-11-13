<script lang="ts">
  // Quick actions (chat-composer look §9.16, F93): the buttons offered over selected answer text.
  // Default keeps the built-in actions; Custom starts from them and can add, edit and remove.
  import { Dialog } from 'bits-ui';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './modal.css';

  type Action = { id: string; label: string; prompt: string };
  type Props = {
    open: boolean;
    /** Nothing means the defaults. */
    actions?: Action[];
    onsave: (actions: Action[] | undefined) => void;
    onclose: () => void;
  };

  let { open, actions, onsave, onclose }: Props = $props();

  // The two built-in actions a custom list starts from.
  const DEFAULTS: Action[] = [
    { id: 'ask', label: 'Ask', prompt: '"{{SELECTED_CONTENT}}"\n\n{{INPUT_CONTENT}}' },
    {
      id: 'explain',
      label: 'Explain',
      prompt: 'Explain this section to me in more detail\n\n```\n{{SELECTED_CONTENT}}\n```',
    },
  ];

  let list = $state<Action[] | undefined>();

  $effect(() => {
    if (open) list = actions ? actions.map((one) => ({ ...one })) : undefined;
  });

  function add() {
    list = [
      ...(list ?? []),
      {
        id: `action_${Date.now()}`,
        label: '',
        prompt: '"{{SELECTED_CONTENT}}"\n\n{{INPUT_CONTENT}}',
      },
    ];
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="card">
        <div class="head">
          <Dialog.Title class="manage-title">Quick Actions</Dialog.Title>
          <Dialog.Close class="manage-close" aria-label="Close modal"
            ><Icon name="x" size={16} /></Dialog.Close
          >
        </div>
        <div class="body">
          <div class="actions-head">
            <span>Actions</span>
            <span class="cluster">
              <button
                type="button"
                onclick={() => (list = list ? undefined : DEFAULTS.map((one) => ({ ...one })))}
                >{list ? 'Custom' : 'Default'}</button
              >
              {#if list}
                <button type="button" aria-label="Add action" onclick={add}
                  ><Icon name="plus" size={16} /></button
                >
              {/if}
            </span>
          </div>
          {#if list}
            {#each list as action, index (index)}
              <div class="action">
                <div class="names">
                  <input
                    bind:value={action.label}
                    placeholder="Button Label"
                    aria-label="Button Label"
                  />
                  <input
                    class="id"
                    bind:value={action.id}
                    placeholder="Button ID"
                    aria-label="Button ID"
                  />
                </div>
                <textarea
                  bind:value={action.prompt}
                  rows="2"
                  placeholder="Button Prompt"
                  aria-label="Button Prompt"></textarea>
                <button
                  type="button"
                  class="remove"
                  aria-label="Remove action"
                  onclick={() => (list = list?.filter((one) => one.id !== action.id))}
                  ><Icon name="minus" size={16} /></button
                >
              </div>
            {/each}
          {:else}
            <p class="default">Default action buttons will be used.</p>
          {/if}
        </div>
        <div class="footer">
          <button type="button" class="save" onclick={() => onsave($state.snapshot(list))}
            >Save</button
          >
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

  .body {
    padding: 0 16px 16px;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  .actions-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .cluster {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--color-gray-500);
  }

  .cluster button {
    display: flex;
  }

  .default {
    padding-block: 20px;
    color: var(--color-gray-500);
    text-align: center;
  }

  .action {
    display: flex;
    align-items: flex-start;
    padding-block: 4px;
  }

  .action + .action {
    margin-block-start: 8px;
    padding-block-start: 12px;
    border-block-start: 1px solid color-mix(in srgb, var(--color-gray-50) 30%, transparent);
  }

  .names {
    display: flex;
    flex-direction: column;
    padding-inline-end: 8px;
  }

  input,
  textarea {
    background: transparent;
    color: inherit;
    font-size: var(--text-caption);
  }

  input {
    inline-size: 80px;
  }

  .id {
    color: var(--color-gray-600);
  }

  textarea {
    flex: 1;
    resize: none;
    field-sizing: content;
  }

  :is(input, textarea):focus {
    outline: none;
  }

  .remove {
    display: flex;
    padding-inline-start: 12px;
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

  :is(.cluster button, .remove, .save):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
