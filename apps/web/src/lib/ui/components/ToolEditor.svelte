<script lang="ts">
  // A tool (workspace look §9.2, F114): name, id and description over the Python code. Creating,
  // the id follows the name, the code header fills empty fields, and saving first asks the person
  // to accept the risk of running code; editing keeps the id and stays on the page.
  import Wire from './Wire.svelte';
  import { untrack } from 'svelte';
  import { resolve } from '$app/paths';
  import type { DataSource, Tool } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { STARTER, manifest, toolId, type ToolDraft } from '$lib/ui/tools';
  import CodeEditor from './CodeEditor.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import RiskNotice from './RiskNotice.svelte';

  type Props = {
    source: DataSource;
    /** The tool being edited; absent when creating. */
    tool?: Tool;
    /** A clone's starting point; its id is kept, not made from the name. */
    draft?: ToolDraft;
    onsaved?: () => void;
  };

  let { source, tool, draft, onsaved }: Props = $props();

  const start = untrack(() => tool ?? draft);
  const editing = untrack(() => tool !== undefined);
  const followName = untrack(() => !tool && !draft);
  const writable = untrack(() => tool?.writable ?? true);

  let name = $state(start?.name ?? '');
  let id = $state(start?.id ?? '');
  let description = $state(start?.description ?? '');
  let content = $state(start?.content || STARTER);
  let problem = $state('');
  let saving = $state(false);
  let confirming = $state(false);

  function rename(value: string) {
    name = value;
    if (followName) id = toolId(value);
  }

  // While creating, the code header fills the name and description only when they are empty.
  function coded(value: string) {
    content = value;
    if (editing) return;
    const meta = manifest(value);
    if (meta.title && !name) rename(meta.title);
    if (meta.description && !description) description = meta.description;
  }

  function submit(event?: SubmitEvent) {
    event?.preventDefault();
    if (!name.trim() || !id.trim() || !description.trim() || !content.trim()) {
      problem = 'Please fill in all fields.';
      return;
    }
    problem = '';
    if (editing) void save();
    else confirming = true;
  }

  async function save() {
    saving = true;
    try {
      if (editing) await source.updateTool(id, { name, description, content });
      else await source.createTool({ id, name, description, content });
      onsaved?.();
    } catch (error) {
      problem = error instanceof Error ? error.message : String(error);
    } finally {
      saving = false;
    }
  }
</script>

<form class="frame" novalidate onsubmit={submit}>
  <a class="back" href={resolve('/workspace/tools')}>
    <Icon name="caret-left" size={12} /><span>Back</span>
  </a>

  <div class="head">
    <div class="identity">
      <input
        class="name"
        value={name}
        oninput={(event) => rename(event.currentTarget.value)}
        placeholder="Tool Name"
        aria-label="Tool Name"
        title="e.g. My Tools"
        disabled={!writable}
        required
      />
      <div class="sub">
        {#if editing}
          <span class="id-text">{id}</span>
        {:else}
          <input
            class="id"
            bind:value={id}
            placeholder="Tool ID"
            aria-label="Tool ID"
            title="e.g. my_tools"
            required
          />
        {/if}
        <input
          class="description"
          bind:value={description}
          placeholder="Tool Description"
          aria-label="Tool Description"
          title="e.g. Tools for a specific task"
          disabled={!writable}
          required
        />
      </div>
    </div>
    <div class="actions">
      <button type="button" class="access">
        <Icon name="lock" size={12} /><span>Access</span>
      </button>
    </div>
  </div>

  <div class="panel">
    <CodeEditor value={content} onchange={coded} onsave={() => submit()} readonly={!writable} />
  </div>

  {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
  <div class="footer">
    <p class="warning">
      <strong>Warning:</strong> Tools can execute arbitrary code.
      <span>Only install tools from sources you trust.</span>
    </p>
    {#if writable}
      <button type="submit" class="save" disabled={saving}>
        {editing ? 'Save' : 'Save & Create'}
        {#if saving}<Wire />{/if}
      </button>
    {/if}
  </div>
</form>

<ConfirmDialog
  open={confirming}
  message=""
  oncancel={() => (confirming = false)}
  onconfirm={() => {
    confirming = false;
    void save();
  }}
>
  <RiskNotice />
</ConfirmDialog>

<style>
  .frame {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
    min-inline-size: 0;
    padding: 0 12px 4px;
    overflow: hidden;
  }

  .back {
    display: flex;
    align-items: center;
    gap: 4px;
    inline-size: fit-content;
    block-size: 24px;
    margin-block-end: 4px;
    border-radius: 6px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: color 75ms;
  }

  .back:hover {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .back {
    color: var(--color-gray-600);
  }

  input {
    background: transparent;
    color: inherit;
  }

  input:focus {
    outline: none;
  }

  input::placeholder {
    color: var(--color-gray-400);
  }

  .head {
    display: flex;
    flex-shrink: 0;
    align-items: flex-start;
    gap: 8px;
    padding: 0 4px 8px;
  }

  .identity {
    flex: 1;
    min-inline-size: 0;
  }

  .name {
    inline-size: 100%;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .sub {
    display: flex;
    gap: 8px;
    margin-block-start: 2px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .id,
  .description {
    flex: 1;
    min-inline-size: 0;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .id {
    min-inline-size: 128px;
    font-family: var(--font-mono);
  }

  .id-text {
    flex-shrink: 0;
    overflow: hidden;
    font-family: var(--font-mono);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .actions {
    display: flex;
    gap: 4px;
    padding-inline-end: 2px;
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

  .panel {
    flex: 1;
    min-block-size: 0;
    overflow: hidden;
    border-radius: 8px;
  }

  .problem {
    margin-block-start: 4px;
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }

  .footer {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding-block: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .warning {
    min-inline-size: 0;
  }

  .warning strong {
    font-weight: 400;
  }

  :global([data-theme='dark']) .warning strong {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .warning span {
    color: var(--color-gray-400);
  }

  .save {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    block-size: 28px;
    padding-inline: 10px;
    border-radius: 8px;
    background-color: var(--color-gray-900);
    color: var(--color-white);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: background-color 150ms;
  }

  .save:hover {
    background-color: var(--color-black);
  }

  .save:disabled {
    opacity: 0.6;
  }

  :global([data-theme='dark']) .save {
    background-color: var(--color-gray-100);
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .save:hover {
    background-color: var(--color-white);
  }

  :is(.back, .access, .save):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
