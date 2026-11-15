<script lang="ts">
  // A skill (workspace look §7.2, F105): name, id and description over the markdown
  // instructions. Creating, the id follows the name and empty fields fill from front matter;
  // editing keeps the id and stays on the page after saving.
  import Wire from './Wire.svelte';
  import { untrack } from 'svelte';
  import { resolve } from '$app/paths';
  import type { DataSource, Skill } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { frontmatter, skillId, titleCase, type SkillDraft } from '$lib/ui/skills';

  type Props = {
    source: DataSource;
    /** The skill being edited; absent when creating. */
    skill?: Skill;
    /** A clone or import's starting point; its id is kept, not made from the name. */
    draft?: SkillDraft;
    onsaved?: () => void;
  };

  let { source, skill, draft, onsaved }: Props = $props();

  const start = untrack(() => skill ?? draft);
  const editing = untrack(() => skill !== undefined);
  const followName = untrack(() => !skill && !draft);
  const writable = untrack(() => skill?.writable ?? true);

  let name = $state(start?.name ?? '');
  let id = $state(start?.id ?? '');
  let description = $state(start?.description ?? '');
  let instructions = $state(start?.instructions ?? '');
  let problem = $state('');
  let saving = $state(false);

  function rename(value: string) {
    name = value;
    if (followName) id = skillId(value);
  }

  // While creating, front matter fills the name and description only when they are empty (F105).
  function typed(value: string) {
    instructions = value;
    if (editing) return;
    const meta = frontmatter(value);
    if (meta.name && !name) rename(titleCase(meta.name));
    if (meta.description && !description) description = meta.description;
  }

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!name.trim() || !id.trim() || !instructions.trim()) {
      problem = 'Please fill in all fields.';
      return;
    }
    problem = '';
    saving = true;
    try {
      // Saving changes the text only, so a switched-off skill stays off (unlike the running app).
      if (editing) await source.updateSkill(id, { name, description, instructions });
      else await source.createSkill({ id, name, description, instructions });
      onsaved?.();
    } catch (error) {
      problem = error instanceof Error ? error.message : String(error);
    } finally {
      saving = false;
    }
  }
</script>

<form class="frame" novalidate onsubmit={submit}>
  <a class="back" href={resolve('/workspace/skills')}>
    <Icon name="caret-left" size={12} /><span>Back</span>
  </a>

  <div class="head">
    <div class="identity">
      <input
        class="name"
        value={name}
        oninput={(event) => rename(event.currentTarget.value)}
        placeholder="Skill Name"
        aria-label="Skill Name"
        title="e.g. Code Review Guidelines"
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
            placeholder="Skill ID"
            aria-label="Skill ID"
            title="e.g. code-review-guidelines"
            required
          />
        {/if}
        <input
          class="description"
          bind:value={description}
          placeholder="Skill Description"
          aria-label="Skill Description"
          title="e.g. Step-by-step instructions for code reviews"
          disabled={!writable}
        />
      </div>
    </div>
    <div class="actions">
      {#if writable}
        <button type="button" class="access">
          <Icon name="lock" size={12} /><span>Access</span>
        </button>
      {:else}
        <span class="read-only">Read Only</span>
      {/if}
    </div>
  </div>

  <div class="panel">
    {#if writable}
      <textarea
        value={instructions}
        oninput={(event) => typed(event.currentTarget.value)}
        placeholder="Enter skill instructions in markdown..."
        aria-label="Instructions"
        required></textarea>
    {:else}
      <pre>{instructions}</pre>
    {/if}
  </div>

  {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
  {#if writable}
    <div class="footer">
      <button type="submit" class="save" disabled={saving}>
        {editing ? 'Save' : 'Save & Create'}
        {#if saving}<Wire />{/if}
      </button>
    </div>
  {/if}
</form>

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

  .read-only {
    padding: 4px 8px;
    border-radius: 8px;
    background-color: var(--color-gray-100);
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .panel {
    flex: 1;
    min-block-size: 0;
    overflow: hidden;
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 60%, transparent);
  }

  :global([data-theme='dark']) .panel {
    background-color: rgb(255 255 255 / 0.03);
  }

  textarea,
  pre {
    inline-size: 100%;
    block-size: 100%;
    margin: 0;
    padding: 8px 12px;
    background: transparent;
    color: inherit;
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    line-height: 1.625;
  }

  textarea {
    resize: none;
  }

  textarea:focus {
    outline: none;
  }

  textarea::placeholder {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) textarea::placeholder {
    color: var(--color-gray-600);
  }

  pre {
    overflow: auto;
    white-space: pre-wrap;
  }

  .problem {
    margin-block-start: 4px;
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }

  .footer {
    display: flex;
    flex-shrink: 0;
    justify-content: flex-end;
    padding-block: 8px;
  }

  .save {
    display: flex;
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
