<script lang="ts">
  // Playground completions (playground look §3): one text box; Run streams the continuation
  // into it.
  import type { DataSource } from '$lib/data';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  let text = $state('');
  let running = $state<AbortController>();

  async function run() {
    if (running) {
      running.abort();
      return;
    }
    const controller = new AbortController();
    running = controller;
    try {
      for await (const piece of source.playgroundStream(
        { kind: 'completion', prompt: text, model: '' },
        controller.signal,
      ))
        text += piece;
    } finally {
      running = undefined;
    }
  }
</script>

<div class="completions">
  <textarea bind:value={text} placeholder="Enter text to complete" aria-label="Text"></textarea>
  <div class="row">
    <button type="button" class="run" onclick={run}>{running ? 'Stop' : 'Run'}</button>
  </div>
</div>

<style>
  .completions {
    display: flex;
    flex-direction: column;
    gap: 8px;
    block-size: 100%;
    padding: 0 10px 10px;
  }
  textarea {
    flex: 1;
    padding: 12px;
    border: 1px solid var(--color-gray-100);
    border-radius: 16px;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    resize: none;
  }
  :global([data-theme='dark']) textarea {
    border-color: var(--color-gray-850);
  }
  textarea:focus {
    outline: none;
  }
  .row {
    display: flex;
    justify-content: flex-end;
  }
  .run {
    padding: 6px 12px;
    border-radius: 8px;
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-ui);
  }

  .run {
    transition: background-color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .run:hover {
    background-color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .run:hover {
    background-color: var(--color-gray-100);
  }
  :global([data-theme='dark']) .run {
    background-color: var(--color-white);
    color: var(--color-black);
  }
</style>
