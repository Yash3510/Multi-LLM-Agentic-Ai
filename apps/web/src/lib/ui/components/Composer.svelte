<script lang="ts">
  // The message box (chat-composer look §4.2, §4.4, §4.8): a 20 px soft box with a hairline border
  // and ring, a 15 px writing area, and the control row: more, integrations, tools on the left;
  // the model, dictation and the round action on the right. Enter sends, Shift+Enter breaks a
  // line, and nothing is sent while an input method is still composing.
  import { m } from '$lib/i18n/generated/messages.js';
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    onsend: (text: string) => void;
    /** The working model or agent, shown on the chip. */
    model: string;
    /** How many tools are on; the count chip shows when there are any. */
    tools?: number;
    placeholder?: string;
    /** The draft, bindable so a suggestion can fill it. */
    value?: string;
  };

  let {
    onsend,
    model,
    tools = 0,
    placeholder = m.composer_placeholder(),
    value = $bindable(''),
  }: Props = $props();
  const ready = $derived(value.trim().length > 0);

  function send() {
    if (!ready) return;
    onsend(value.trim());
    value = '';
  }

  function keydown(event: KeyboardEvent) {
    if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
    event.preventDefault();
    send();
  }
</script>

<div class="box">
  <div class="editor">
    <textarea bind:value aria-label={m.composer_label()} {placeholder} rows="1" onkeydown={keydown}
    ></textarea>
  </div>
  <div class="controls">
    <div class="start">
      <button type="button" class="round" aria-label={m.composer_more()} title={m.composer_more()}>
        <Icon name="plus" size={20} />
      </button>
      <span class="divider" aria-hidden="true"></span>
      <button
        type="button"
        class="round"
        aria-label={m.composer_integrations()}
        title={m.composer_integrations()}
      >
        <Icon name="integrations" size={18} />
      </button>
      {#if tools > 0}
        <button type="button" class="chip" aria-label={m.composer_tools({ count: tools })}>
          <Icon name="tools" size={16} />
          <span class="tabular">{tools}</span>
        </button>
      {/if}
    </div>
    <div class="end">
      <button type="button" class="model" aria-label={m.composer_model({ model })}>
        <span class="brand">{m.app_name()}</span>
        <span class="truncate">{model}</span>
        <Icon name="caret-down" size={10} />
      </button>
      <button
        type="button"
        class="round"
        aria-label={m.composer_dictate()}
        title={m.composer_dictate()}
      >
        <Icon name="microphone" size={18} />
      </button>
      {#if ready}
        <button type="button" class="action" aria-label={m.composer_send()} onclick={send}>
          <Icon name="send" size={18} />
        </button>
      {:else}
        <button type="button" class="action" aria-label={m.composer_voice_mode()}>
          <Icon name="voice-mode" size={18} />
        </button>
      {/if}
    </div>
  </div>
</div>

<style>
  .box {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    padding-inline: 2px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 30%, transparent);
    border-radius: 20px;
    background-color: color-mix(in srgb, var(--color-white) 5%, transparent);
    box-shadow:
      0 0 0 1px rgb(0 0 0 / 0.04),
      0 1px 2px -1px rgb(16 24 40 / 0.06),
      0 12px 32px -14px rgb(16 24 40 / 0.2);
    backdrop-filter: blur(4px);
    transition:
      border-color 300ms ease-out,
      box-shadow 300ms ease-out;
  }

  .box:hover {
    border-color: var(--color-gray-200);
  }

  .box:focus-within {
    border-color: var(--color-gray-100);
    box-shadow:
      0 0 0 1px rgb(0 0 0 / 0.08),
      0 1px 3px -1px rgb(16 24 40 / 0.08),
      0 20px 48px -18px rgb(16 24 40 / 0.28);
  }

  :global([data-theme='dark']) .box {
    border-color: color-mix(in srgb, var(--color-gray-850) 30%, transparent);
    background-color: color-mix(in srgb, var(--color-gray-500) 5%, transparent);
    box-shadow:
      0 0 0 1px rgb(255 255 255 / 0.06),
      0 1px 2px -1px rgb(16 24 40 / 0.06),
      0 12px 32px -14px rgb(16 24 40 / 0.2);
    color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .box:is(:hover, :focus-within) {
    border-color: var(--color-gray-800);
  }

  .editor {
    padding-inline: var(--spacing-2);
  }

  textarea {
    display: block;
    inline-size: 100%;
    max-block-size: 384px;
    padding: var(--spacing-2) var(--spacing-1) 2px;
    border: 0;
    background: transparent;
    color: inherit;
    font-size: var(--text-body);
    line-height: 1.75;
    resize: none;
    field-sizing: content;
    scrollbar-width: none;
  }

  textarea:focus-visible {
    outline: none;
  }

  textarea::placeholder {
    color: var(--color-ink-3);
  }

  .controls {
    display: flex;
    justify-content: space-between;
    margin: 2px 2px var(--spacing-2);
  }

  .start,
  .end {
    display: flex;
    align-items: flex-end;
  }

  .start {
    flex: 1;
    min-inline-size: 0;
    margin-inline-start: var(--spacing-1);
  }

  .end {
    gap: 4.5px;
    margin-inline-end: var(--spacing-1);
  }

  .round,
  .action {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 30px;
    block-size: 30px;
    border-radius: var(--radius-pill);
    color: var(--color-gray-700);
    transition: background-color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global([data-theme='dark']) .round {
    color: var(--color-white);
  }

  .round:hover,
  .chip:hover,
  .model:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) :is(.round, .chip, .model):hover {
    background-color: var(--color-gray-800);
  }

  .divider {
    align-self: center;
    inline-size: 1px;
    block-size: 16px;
    margin-inline: var(--spacing-1);
    background-color: color-mix(in srgb, var(--color-gray-200) 50%, transparent);
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    block-size: 30px;
    padding-inline: var(--spacing-2) 10px;
    border-radius: var(--radius-pill);
    color: var(--color-gray-600);
    font-size: var(--text-small);
  }

  .model {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    max-inline-size: 208px;
    block-size: 30px;
    padding-inline: var(--spacing-2);
    border-radius: var(--radius-pill);
    color: var(--color-ink-3);
    font-size: var(--text-small);
  }

  .brand {
    color: var(--color-ink-1);
    font-weight: var(--font-weight-semibold);
  }

  .action {
    background-color: var(--color-solid);
    color: var(--color-on-solid);
  }

  :is(.round, .chip, .model, .action):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }
</style>
