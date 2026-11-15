<script lang="ts">
  // Add text content (workspace look §5.5, F82): a full-screen page with a large title and the
  // text under it. Save turns it into a .txt document named after the title.
  import { Dialog } from 'bits-ui';
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    open: boolean;
    onsave: (title: string, text: string) => Promise<void>;
    onclose: () => void;
  };

  let { open, onsave, onclose }: Props = $props();

  let title = $state('');
  let text = $state('');
  let problem = $state('');

  async function save() {
    if (!title.trim() || !text.trim()) {
      problem = 'Please fill in all fields.';
      return;
    }
    await onsave(title.trim(), text.trim());
    title = '';
    text = '';
    problem = '';
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Content class="composer" aria-describedby={undefined}>
      <Dialog.Title class="sr-only">Add text content</Dialog.Title>
      <Dialog.Close class="composer-close" aria-label="Close"
        ><Icon name="x" size={14} /></Dialog.Close
      >
      <div class="scroll">
        <div class="column">
          <input class="title" bind:value={title} placeholder="Title" aria-label="Title" />
          <textarea
            class="text"
            bind:value={text}
            placeholder="Write something..."
            aria-label="Content"></textarea>
        </div>
      </div>
      {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
      <div class="footer">
        <button type="button" class="save" title="Save" onclick={save}>Save</button>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  :global(.composer) {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--color-white);
    background-color: var(--color-white);
  }

  :global([data-theme='dark'] .composer) {
    border-color: var(--color-gray-850);
    background-color: var(--color-gray-900);
    color: var(--color-gray-200);
  }

  :global(.composer-close) {
    position: absolute;
    inset-block-start: 0;
    inset-inline-end: 0;
    display: grid;
    padding: 20px;
  }

  .scroll {
    display: flex;
    flex: 1;
    justify-content: center;
    padding: 16px 20px;
    overflow-y: auto;
  }

  .column {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 8px;
    max-inline-size: 768px;
    padding-block: 8px;
  }

  @media (min-width: 48rem) {
    .column {
      padding-block: 40px;
    }
  }

  .title,
  .text {
    inline-size: 100%;
    background: transparent;
    color: inherit;
  }

  :is(.title, .text):focus {
    outline: none;
  }

  :is(.title, .text)::placeholder {
    color: var(--color-gray-500);
  }

  :global([data-theme='dark']) :is(.title, .text)::placeholder {
    color: var(--color-gray-600);
  }

  .title {
    font-size: var(--text-figure);
    line-height: 36px;
  }

  .text {
    flex: 1;
    min-block-size: 200px;
    font-size: 16px;
    line-height: 26px;
    resize: none;
  }

  .problem {
    padding-inline: 16px;
    color: var(--color-red-600);
    font-size: var(--text-caption);
    text-align: end;
  }

  .footer {
    display: flex;
    justify-content: flex-end;
    gap: 6px;
    margin-block-start: 4px;
    padding: 16px;
    font-size: var(--text-ui);
  }

  .save {
    padding: 8px 14px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
    transition: background-color 150ms;
  }

  :global([data-theme='dark']) .save {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :global(.composer-close:focus-visible),
  .save:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
