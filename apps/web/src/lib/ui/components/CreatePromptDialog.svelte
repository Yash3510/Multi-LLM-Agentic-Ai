<script lang="ts">
  // Create prompt (workspace look §6.2, F93): a near-full-window card with the name and access,
  // the slash command (made from the name until typed), tags, and the prompt text.
  import { Dialog } from 'bits-ui';
  import { untrack } from 'svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { COMMAND_RULE, commandFrom, isCommand, type PromptDraft } from '$lib/ui/prompts';
  import TagInput from './TagInput.svelte';
  import './modal.css';

  type Props = {
    open: boolean;
    /** A clone's starting point. */
    prefill?: PromptDraft;
    oncreate: (draft: PromptDraft) => Promise<void>;
    onclose: () => void;
  };

  let { open, prefill, oncreate, onclose }: Props = $props();

  let name = $state(untrack(() => prefill?.name ?? ''));
  let command = $state(untrack(() => prefill?.command ?? ''));
  let tags = $state(untrack(() => [...(prefill?.tags ?? [])]));
  let content = $state(untrack(() => prefill?.content ?? ''));
  // The command follows the name until it is typed in (F93).
  let typed = false;
  let problem = $state('');
  let saving = $state(false);

  function rename(value: string) {
    name = value;
    if (!typed) command = commandFrom(value);
  }

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!isCommand(command)) {
      problem = COMMAND_RULE;
      return;
    }
    if (!name.trim() || !content.trim()) {
      problem = 'Please fill in all fields.';
      return;
    }
    problem = '';
    saving = true;
    try {
      await oncreate({ name: name.trim(), command, content, tags });
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
      <div class="card">
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}<h3 {...props} class="prompt-title">
                Create Prompt
              </h3>{/snippet}
          </Dialog.Title>
          <Dialog.Close class="prompt-close" aria-label="Close"
            ><Icon name="x" size={20} /></Dialog.Close
          >
        </div>
        <form novalidate onsubmit={submit}>
          <div
            class="identity"
            title="Only alphanumeric characters and hyphens are allowed. Activate this command by typing / followed by it in the chat input."
          >
            <div class="name-row">
              <input
                class="name"
                value={name}
                oninput={(event) => rename(event.currentTarget.value)}
                placeholder="Name"
                aria-label="Name"
                required
              />
              <button type="button" class="access">
                <Icon name="lock" size={12} /><span>Access</span>
              </button>
            </div>
            <div class="command-row">
              <span aria-hidden="true">/</span>
              <input
                class="command"
                bind:value={command}
                oninput={() => (typed = true)}
                placeholder="Command"
                aria-label="Command"
                required
              />
            </div>
            <div class="tags"><TagInput bind:tags /></div>
          </div>
          <label class="caption" for="prompt-content">Prompt Content</label>
          <textarea
            id="prompt-content"
            class="content"
            bind:value={content}
            placeholder={'Write a summary in 50 words that summarizes {{topic}}.'}
            required></textarea>
          <p class="hint">
            ⓘ Use <span class="token">{'{{variable}}'}</span> for placeholders
          </p>
          {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
          <div class="footer">
            <button type="button" class="cancel" onclick={onclose}>Cancel</button>
            <button type="submit" class="create" disabled={saving}>
              Save & Create
              {#if saving}<span class="spinner" aria-hidden="true"></span>{/if}
            </button>
          </div>
        </form>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  /* The window less 32, 48 or 64 px, never over 1280 px; at most 864 px tall (look §6.2). */
  .card {
    display: flex;
    flex-direction: column;
    inline-size: min(calc(100vw - 32px), 1280px);
    block-size: min(864px, calc(100vh - 64px));
    margin: auto;
    border: 1px solid var(--color-white);
    border-radius: 32px;
    background-color: var(--color-white);
  }

  @media (min-width: 40rem) {
    .card {
      inline-size: min(calc(100vw - 48px), 1280px);
    }
  }

  @media (min-width: 64rem) {
    .card {
      inline-size: min(calc(100vw - 64px), 1280px);
    }
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
    padding: 16px 20px 8px;
  }

  :global(.prompt-title) {
    font-size: var(--text-ui);
    font-weight: 400;
    line-height: 20px;
  }

  :global(.prompt-close) {
    display: grid;
    margin-inline-start: 8px;
  }

  form {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
    padding: 0 20px 12px;
  }

  input,
  textarea {
    background: transparent;
    color: inherit;
  }

  :is(input, textarea):focus {
    outline: none;
  }

  :is(input, textarea)::placeholder {
    color: var(--color-gray-400);
  }

  .identity {
    margin-block-end: 8px;
  }

  .name-row {
    display: flex;
    align-items: center;
  }

  .name {
    flex: 1;
    min-inline-size: 0;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .access {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    color: var(--color-gray-900);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: background-color 150ms;
  }

  .access:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .access {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
    color: var(--color-gray-100);
  }

  .command-row {
    display: flex;
    gap: 2px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .command {
    flex: 1;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  /* The running app sets the tag field 10 px under the command. */
  .tags {
    margin-block-start: 10px;
  }

  /* 18 px under the tags with the block's 8 px margin, as the running app measures. */
  .caption {
    margin-block: 10px 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .content {
    flex: 1;
    min-block-size: 0;
    font-size: var(--text-caption);
    line-height: 16px;
    resize: none;
  }

  .hint {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .token {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .hint {
    color: var(--color-gray-500);
  }

  :global([data-theme='dark']) .token {
    color: var(--color-gray-300);
  }

  .problem {
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }

  .footer {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    padding-block-start: 20px;
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

  .create {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: background-color 150ms;
  }

  .create:hover {
    background-color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .create {
    background-color: var(--color-white);
    color: var(--color-black);
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

  :global(.prompt-close:focus-visible),
  :is(.access, .cancel, .create):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
