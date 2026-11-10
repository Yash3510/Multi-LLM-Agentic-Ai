<script lang="ts">
  // The playground chat (playground look §3): system instructions, an editable list of user and
  // assistant messages, and the composer with role, model, Add and Run. Run streams the model's
  // reply from the data source.
  import type { DataSource } from '$lib/data';
  import type { ParamValue } from '$lib/ui/params';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import AdvancedParams from './AdvancedParams.svelte';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  type Turn = { role: 'user' | 'assistant'; content: string };
  let system = $state('');
  let editingSystem = $state(false);
  let turns = $state<Turn[]>([]);
  let draft = $state('');
  let role = $state<Turn['role']>('user');
  let models = $state<{ id: string; name: string }[]>([]);
  let model = $state('');
  let running = $state<AbortController>();
  let showParams = $state(false);
  let params = $state<Record<string, ParamValue>>({});

  async function loadModels() {
    models = await source.listBaseModels();
    model = models[0]?.id ?? '';
  }
  void loadModels();

  function add() {
    if (!draft.trim()) return;
    turns = [...turns, { role, content: draft }];
    draft = '';
    role = role === 'user' ? 'assistant' : 'user';
  }

  async function run() {
    if (running) {
      running.abort();
      return;
    }
    if (draft.trim()) add();
    const controller = new AbortController();
    running = controller;
    const reply: Turn = { role: 'assistant', content: '' };
    turns = [...turns, reply];
    const index = turns.length - 1;
    try {
      for await (const piece of source.playgroundStream(
        { kind: 'chat', system, messages: $state.snapshot(turns).slice(0, -1), model },
        controller.signal,
      ))
        turns[index].content += piece;
    } finally {
      running = undefined;
      role = 'user';
    }
  }
</script>

<div class="playground">
  <div class="system">
    {#if editingSystem}
      <textarea
        bind:value={system}
        rows="2"
        placeholder="You are a helpful assistant."
        aria-label="System Instructions"></textarea>
    {:else}
      <span>{system || 'System Instructions'}</span>
    {/if}
    <button
      type="button"
      class="icon"
      aria-label="Edit system instructions"
      onclick={() => (editingSystem = !editingSystem)}><Icon name="rename" size={14} /></button
    >
  </div>
  <div class="turns">
    {#each turns as turn, index (index)}
      <div class="turn">
        <div class="turn-head">
          <button
            type="button"
            class="role"
            onclick={() => (turn.role = turn.role === 'user' ? 'assistant' : 'user')}
            >{turn.role}</button
          >
          <button
            type="button"
            class="icon"
            aria-label="Delete message"
            onclick={() => (turns = turns.filter((_, at) => at !== index))}
            ><Icon name="x" size={14} /></button
          >
        </div>
        <textarea class="turn-text" bind:value={turn.content} aria-label="Message" rows="1"
        ></textarea>
        <p class="sr-only">{turn.content}</p>
      </div>
    {/each}
  </div>
  {#if showParams}
    <div class="params"><AdvancedParams bind:params /></div>
  {/if}
  <div class="composer">
    <textarea
      bind:value={draft}
      placeholder="Enter a user message here"
      aria-label="New message"
      rows="2"></textarea>
    <div class="row">
      <button
        type="button"
        class="soft"
        onclick={() => (role = role === 'user' ? 'assistant' : 'user')}
        >{role === 'user' ? 'User' : 'Assistant'}</button
      >
      <span class="grow"></span>
      <select class="model" bind:value={model} aria-label="Model">
        {#each models as one (one.id)}<option value={one.id}>{one.name}</option>{/each}
      </select>
      <button
        type="button"
        class="icon"
        aria-label="Parameters"
        aria-pressed={showParams}
        onclick={() => (showParams = !showParams)}><Icon name="sliders-bold" size={14} /></button
      >
      <button type="button" class="soft" onclick={add}>Add</button>
      <button type="button" class="run" onclick={run}>{running ? 'Stop' : 'Run'}</button>
    </div>
  </div>
</div>

<style>
  .params {
    max-block-size: 40%;
    padding: 8px 12px;
    overflow-y: auto;
    border: 1px solid var(--color-gray-100);
    border-radius: 12px;
  }
  .playground {
    display: flex;
    flex-direction: column;
    gap: 8px;
    block-size: 100%;
    padding: 0 10px 10px;
    font-size: var(--text-ui);
  }
  .system {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    border: 1px solid var(--color-gray-100);
    border-radius: 12px;
  }
  :global([data-theme='dark']) .system,
  :global([data-theme='dark']) .composer {
    border-color: var(--color-gray-850);
  }
  .system textarea {
    flex: 1;
  }
  textarea {
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    resize: none;
    field-sizing: content;
  }
  textarea:focus {
    outline: none;
  }
  textarea::placeholder {
    color: var(--color-gray-400);
  }
  .icon {
    display: grid;
    color: var(--color-gray-500);
  }
  .turns {
    flex: 1;
    overflow-y: auto;
  }
  .turn {
    padding: 8px 4px;
    border-block-end: 1px solid var(--color-gray-50);
  }
  .turn-head {
    display: flex;
    justify-content: space-between;
  }
  .role {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-transform: uppercase;
  }
  .turn-text {
    inline-size: 100%;
  }
  .composer {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    border: 1px solid var(--color-gray-100);
    border-radius: 16px;
  }
  .row {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .grow {
    flex: 1;
  }
  .soft {
    padding: 6px 14px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
  }
  :global([data-theme='dark']) .soft {
    background-color: var(--color-gray-850);
  }
  .model {
    inline-size: 188px;
    block-size: 28px;
    padding-inline: 10px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background: transparent;
    color: inherit;
    font-size: var(--text-caption);
  }
  .run {
    padding: 6px 12px;
    border-radius: 8px;
    background-color: var(--color-black);
    color: var(--color-white);
  }
  :global([data-theme='dark']) .run {
    background-color: var(--color-white);
    color: var(--color-black);
  }
  /* Hover states (common look, Motion: playground): 150 ms on the standard curve. */
  :is(.icon, .soft, .run) {
    transition-property: background-color, color;
    transition-duration: 150ms;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }

  .icon:hover {
    color: var(--color-gray-700);
  }

  .soft:hover {
    background-color: var(--color-gray-100);
  }

  .run:hover {
    background-color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .icon:hover {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .soft:hover {
    background-color: var(--color-gray-800);
  }

  :global([data-theme='dark']) .run:hover {
    background-color: var(--color-gray-100);
  }

  :is(.icon, .role, .soft, .run):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
