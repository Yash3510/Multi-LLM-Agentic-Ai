<script lang="ts">
  // Create or edit an automation (automations look §2): name, prompt, model, schedule,
  // destination, status, and the runs so far. Webhook triggers are left out, as the owner chose.
  import { untrack } from 'svelte';
  import { resolve } from '$app/paths';
  import type { Automation, AutomationDraft, DataSource } from '$lib/data';
  import Switch from './Switch.svelte';

  type Props = { source: DataSource; automation?: Automation; onsaved: () => void };

  let { source, automation, onsaved }: Props = $props();

  const start = untrack(() => automation);
  let draft = $state<AutomationDraft>(
    start
      ? {
          id: start.id,
          name: start.name,
          prompt: start.prompt,
          model: start.model,
          schedule: { ...start.schedule },
          destination: start.destination,
          active: start.active,
        }
      : {
          name: '',
          prompt: '',
          model: '4ce-tony',
          schedule: { kind: 'daily', time: '09:00' },
          destination: 'chat',
          active: true,
        },
  );
  let models = $state<{ id: string; name: string }[]>([]);
  let problem = $state('');

  async function loadModels() {
    models = await source.listBaseModels();
  }
  void loadModels();

  async function save(event: SubmitEvent) {
    event.preventDefault();
    if (!draft.name.trim() || !draft.prompt.trim()) {
      problem = 'Give the automation a name and a prompt.';
      return;
    }
    await source.saveAutomation($state.snapshot(draft) as AutomationDraft);
    onsaved();
  }
</script>

<form class="editor" onsubmit={save}>
  <a class="back" href={resolve('/automations')}>Back</a>
  <input
    class="name"
    bind:value={draft.name}
    placeholder="Automation name"
    aria-label="Automation name"
  />
  <label class="field"
    ><span>Prompt</span>
    <textarea bind:value={draft.prompt} placeholder="What should the model do each time?" rows="5"
    ></textarea></label
  >
  <div class="grid">
    <label class="field"
      ><span>Model</span>
      <select bind:value={draft.model}
        >{#each models as one (one.id)}<option value={one.id}>{one.name}</option>{/each}</select
      ></label
    >
    <label class="field"
      ><span>Schedule</span>
      <select bind:value={draft.schedule.kind}>
        <option value="once">Once</option><option value="hourly">Hourly</option><option
          value="daily">Daily</option
        ><option value="weekly">Weekly</option><option value="weekdays">Monday – Friday</option
        ><option value="monthly">Monthly</option><option value="custom">Custom</option>
      </select></label
    >
    {#if draft.schedule.kind === 'custom'}
      <label class="field"
        ><span>Every (minutes)</span><input
          type="number"
          min="1"
          value={draft.schedule.every ?? 60}
          oninput={(e) => (draft.schedule.every = Number(e.currentTarget.value))}
        /></label
      >
    {:else}
      <label class="field"
        ><span>Time</span><input type="time" bind:value={draft.schedule.time} /></label
      >
    {/if}
    <label class="field"
      ><span>Destination</span>
      <select bind:value={draft.destination}
        ><option value="chat">New chat</option><option value="channel">Channel</option></select
      ></label
    >
  </div>
  <div class="status">
    <span>Status: {draft.active ? 'Active' : 'Paused'}</span><Switch
      on={draft.active}
      label="Active"
      onchange={(next) => (draft.active = next)}
    />
  </div>
  <section class="runs">
    <h2>Runs</h2>
    {#each start?.runs ?? [] as run, index (index)}
      <p>
        {run.at.toLocaleString('en-US')}{#if run.chatId}
          · <a href={resolve('/c/[id]', { id: run.chatId })}>View chat</a>{/if}
      </p>
    {:else}
      <p class="none">No runs yet</p>
    {/each}
  </section>
  {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
  <div class="footer"><button type="submit" class="save">Save</button></div>
</form>

<style>
  .editor {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-inline-size: 720px;
    padding: 8px 16px 16px;
    font-size: var(--text-ui);
  }
  .back {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
  }
  .name {
    background: transparent;
    color: inherit;
    font-size: var(--text-base);
  }
  .name:focus,
  textarea:focus {
    outline: none;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .field span,
  .runs h2 {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    font-weight: 400;
  }
  textarea,
  select,
  input[type='time'] {
    padding: 6px 8px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: inherit;
    font-size: var(--text-caption);
  }
  textarea {
    resize: vertical;
    font-size: var(--text-ui);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
  }
  .status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: var(--text-caption);
  }
  .runs p {
    font-size: var(--text-caption);
  }
  .runs a {
    text-decoration: underline;
  }
  .none {
    color: var(--color-gray-500);
  }
  .problem {
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }
  .footer {
    display: flex;
    justify-content: flex-end;
  }
  .save {
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
  }
  :global([data-theme='dark']) .save {
    background-color: var(--color-white);
    color: var(--color-black);
  }
</style>
