<script lang="ts">
  // The model editor (workspace look §3, features F34 to F54): the identity block, model params,
  // prompt suggestions, the knowledge, tool and skill pickers, the capability checklists, Save and
  // the JSON preview. The rules live in model-editor.ts; this file is the look.
  import Wire from './Wire.svelte';
  import { Popover } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { ModelRecord, WorkspaceItem } from '$lib/data';
  import white from '$lib/ui/brand/4ce-logomark-white.svg';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import {
    BUILTIN_TOOLS,
    blankDraft,
    defaultFeatureChoices,
    label,
    matching,
    modelId,
    payload,
    shownCapabilities,
    validate,
    type Feature,
  } from '$lib/ui/model-editor';
  import TagInput from './TagInput.svelte';
  import Typeahead from './Typeahead.svelte';

  type Props = {
    baseModels: WorkspaceItem[];
    knowledge: WorkspaceItem[];
    tools: WorkspaceItem[];
    skills: WorkspaceItem[];
    onsave: (record: ModelRecord) => Promise<void>;
  };

  let { baseModels, knowledge, tools, skills, onsave }: Props = $props();

  // Two lines like the running app's hint, with a 4CE example in place of its upstream one.
  const SYSTEM_HINT =
    'Write your model system prompt content here\n e.g.) You are a plant maintenance assistant. Answer from the manuals.';

  const draft = $state(blankDraft());
  let advanced = $state(false);
  let json = $state(false);
  let saving = $state(false);
  let problem = $state('');
  let baseOpen = $state(false);
  let baseQuery = $state('');
  let knowledgeOpen = $state(false);
  let knowledgeQuery = $state('');

  const baseName = $derived(baseModels.find((model) => model.id === draft.base)?.name);
  const features = $derived(defaultFeatureChoices(draft.capabilities));
  const preview = $derived(JSON.stringify(payload(draft, 'create'), null, 2));

  function rename(event: Event) {
    draft.name = (event.currentTarget as HTMLInputElement).value;
    draft.id = modelId(draft.name);
  }

  function toggleFeature(id: Feature) {
    draft.defaultFeatures = draft.defaultFeatures.includes(id)
      ? draft.defaultFeatures.filter((one) => one !== id)
      : [...draft.defaultFeatures, id];
  }

  function addSuggestion() {
    const list = draft.suggestions ?? [];
    // A blank last entry is not stacked on (F41).
    if (list.length && !list[list.length - 1].content.trim()) return;
    draft.suggestions = [...list, { title: ['', ''], content: '' }];
  }

  async function save(event: SubmitEvent) {
    event.preventDefault();
    problem = validate(draft) ?? '';
    if (problem) return;
    saving = true;
    try {
      await onsave(payload(draft, 'create'));
    } catch (error) {
      problem = error instanceof Error ? error.message : String(error);
    } finally {
      saving = false;
    }
  }
</script>

{#snippet check(checked: boolean, name: string, onclick: () => void)}
  <span class="item">
    <button
      type="button"
      class="box"
      role="checkbox"
      aria-checked={checked}
      aria-label={name}
      data-checked={checked ? '' : undefined}
      {onclick}
    >
      {#if checked}<Icon name="check-bold" size={14} />{/if}
    </button>
    <button type="button" class="item-label" tabindex="-1" {onclick}>{name}</button>
  </span>
{/snippet}

{#snippet picked(items: WorkspaceItem[], ids: string[], onchange: (ids: string[]) => void)}
  {#if ids.length}
    <div class="picked">
      {#each ids as id (id)}
        {@const item = items.find((one) => one.id === id)}
        <span class="picked-item">
          {@render check(true, item?.name ?? id, () => onchange(ids.filter((one) => one !== id)))}
        </span>
      {/each}
      <button type="button" class="clear-all" onclick={() => onchange([])}>Disable all</button>
    </div>
  {/if}
{/snippet}

<div class="frame">
  <a class="back" href={resolve('/workspace/models')}>
    <Icon name="caret-left" size={12} /><span>Back</span>
  </a>

  <div class="scroll">
    <form novalidate onsubmit={save}>
      <div class="identity">
        <div class="head">
          <button type="button" class="avatar" aria-label="Upload profile image">
            <span class="tile"><img src={white} alt="" /></span>
          </button>
          <div class="names">
            <div class="name-row">
              <input
                class="name"
                value={draft.name}
                oninput={rename}
                placeholder="Model Name"
                aria-label="Model Name"
                required
              />
              <button type="button" class="access">
                <Icon name="lock" size={12} /><span>Access</span>
              </button>
            </div>
            <input
              class="id"
              bind:value={draft.id}
              placeholder="Model ID"
              aria-label="Model ID"
              required
            />
          </div>
        </div>

        <div>
          <div class="caption">Base Model (From)</div>
          <div class="base">
            <Popover.Root bind:open={baseOpen} onOpenChange={(next) => !next && (baseQuery = '')}>
              <Popover.Trigger class="base-trigger">
                <span class="truncate">
                  {baseName ?? 'Select a base model (e.g. llama3, gpt-4o)'}
                </span>
                <Icon name="caret-down-bold" size={10} />
              </Popover.Trigger>
              <Popover.Portal>
                <Popover.Content class="base-panel" side="bottom" align="start" sideOffset={4}>
                  <label class="base-search">
                    <Icon name="magnifying-glass-bold" size={14} />
                    <input
                      bind:value={baseQuery}
                      placeholder="Search a model"
                      aria-label="Search a model"
                    />
                  </label>
                  <div class="base-list" role="listbox" aria-label="Base Model">
                    {#each matching(baseModels, baseQuery) as model (model.id)}
                      <button
                        type="button"
                        class="base-row"
                        role="option"
                        aria-selected={model.id === draft.base}
                        onclick={() => {
                          draft.base = model.id;
                          baseOpen = false;
                        }}
                      >
                        <img src={white} alt="" class="base-mark" />
                        <span class="truncate">{model.name}</span>
                      </button>
                    {:else}
                      <p class="base-empty">No results found</p>
                    {/each}
                  </div>
                </Popover.Content>
              </Popover.Portal>
            </Popover.Root>
          </div>
        </div>

        <div>
          <div class="caption-row">
            <span class="caption">Description</span>
            <button
              type="button"
              class="toggle"
              aria-pressed={draft.description.custom}
              onclick={() => (draft.description.custom = !draft.description.custom)}
              >{draft.description.custom ? 'Custom' : 'Default'}</button
            >
          </div>
          {#if draft.description.custom}
            <textarea
              class="description"
              bind:value={draft.description.text}
              rows="2"
              placeholder="Add a short description about what this model does"
              aria-label="Description"></textarea>
          {/if}
        </div>

        <div class="tags"><TagInput bind:tags={draft.tags} /></div>
      </div>

      <section class="params">
        <div class="caption params-caption">Model Params</div>
        <div class="sub-caption">System Prompt</div>
        <textarea
          class="system"
          bind:value={draft.system}
          rows="2"
          placeholder={SYSTEM_HINT}
          aria-label="System Prompt"></textarea>
        <div class="advanced">
          <span class="sub-caption">Advanced Params</span>
          <button type="button" class="toggle" onclick={() => (advanced = !advanced)}
            >{advanced ? 'Hide' : 'Show'}</button
          >
        </div>
      </section>

      <hr class="rule first" />

      <section class="prompts" role="group" aria-label="Prompts">
        <div class="caption-row">
          <span class="caption">Prompts</span>
          <button
            type="button"
            class="toggle"
            onclick={() =>
              (draft.suggestions = draft.suggestions ? null : [{ title: ['', ''], content: '' }])}
            >{draft.suggestions ? 'Custom' : 'Default'}</button
          >
        </div>
        {#if draft.suggestions}
          <div class="suggestions">
            <div class="suggestions-head">
              <span>Default Prompt Suggestions</span>
              <button
                type="button"
                class="add"
                aria-label="Add prompt suggestion"
                onclick={addSuggestion}><Icon name="plus-bold" size={14} /></button
              >
            </div>
            {#each draft.suggestions as suggestion, index (index)}
              <div class="suggestion">
                <div class="suggestion-fields">
                  <div class="suggestion-titles">
                    <input
                      bind:value={suggestion.title[0]}
                      placeholder="Title"
                      aria-label="Title"
                    />
                    <input
                      class="subtitle"
                      bind:value={suggestion.title[1]}
                      placeholder="Subtitle"
                      aria-label="Subtitle"
                    />
                  </div>
                  <textarea
                    bind:value={suggestion.content}
                    rows="1"
                    placeholder="Prompt"
                    aria-label="Prompt"></textarea>
                </div>
                <button
                  type="button"
                  class="remove"
                  aria-label="Remove prompt suggestion"
                  onclick={() => draft.suggestions?.splice(index, 1)}
                  ><Icon name="x" size={14} /></button
                >
              </div>
            {:else}
              <p class="none">No suggestion prompts</p>
            {/each}
          </div>
        {/if}
      </section>

      <section class="block">
        <div class="block-head">
          <span class="title">Knowledge</span>
          <Popover.Root
            bind:open={knowledgeOpen}
            onOpenChange={(next) => !next && (knowledgeQuery = '')}
          >
            <Popover.Trigger class="typeahead-trigger">Select Knowledge</Popover.Trigger>
            <Popover.Portal>
              <Popover.Content
                class="typeahead knowledge-panel"
                side="bottom"
                align="start"
                sideOffset={4}
              >
                <label class="base-search">
                  <Icon name="magnifying-glass" size={14} />
                  <input bind:value={knowledgeQuery} placeholder="Search" aria-label="Search" />
                </label>
                <div class="base-list">
                  {#each matching(knowledge, knowledgeQuery) as item (item.id)}
                    <button
                      type="button"
                      class="knowledge-row"
                      onclick={() => {
                        if (!draft.knowledge.some((one) => one.id === item.id))
                          draft.knowledge.push({ id: item.id, name: item.name });
                        knowledgeOpen = false;
                      }}><Icon name="database" size={14} />{item.name}</button
                    >
                  {:else}
                    <p class="none-found">No knowledge found</p>
                  {/each}
                </div>
              </Popover.Content>
            </Popover.Portal>
          </Popover.Root>
          <button type="button" class="link">Upload</button>
        </div>
        {#if draft.knowledge.length}
          <div class="chips">
            {#each draft.knowledge as item (item.id)}
              <span class="chip">
                <Icon name="database" size={14} /><span class="truncate">{item.name}</span>
                <button
                  type="button"
                  aria-label="Remove File"
                  onclick={() =>
                    (draft.knowledge = draft.knowledge.filter((one) => one.id !== item.id))}
                  ><Icon name="x" size={12} /></button
                >
              </span>
            {/each}
            <button type="button" class="clear-all" onclick={() => (draft.knowledge = [])}
              >Disable all</button
            >
          </div>
        {/if}
        <p class="help">
          To attach knowledge base here, add them to the "Knowledge" workspace first.
        </p>
      </section>

      <section class="block">
        <div class="block-head">
          <span class="title">Tools</span>
          {#if tools.length}
            <Typeahead
              label="Select Tool"
              search="Search tools"
              empty="No tools found"
              items={tools}
              selected={draft.tools}
              onchange={(ids) => (draft.tools = ids)}
            />
          {/if}
        </div>
        {@render picked(tools, draft.tools, (ids) => (draft.tools = ids))}
        <p class="help">
          To select toolkits here, add them to the "Tools" workspace or enable a tool server first.
        </p>
      </section>

      <section class="block">
        <div class="block-head">
          <span class="title">Skills</span>
          {#if skills.length}
            <Typeahead
              label="Select Skill"
              search="Search skills"
              empty="No skills found"
              items={skills}
              selected={draft.skills}
              onchange={(ids) => (draft.skills = ids)}
            />
          {/if}
        </div>
        {@render picked(skills, draft.skills, (ids) => (draft.skills = ids))}
        <p class="help tight">To select skills here, add them to the "Skills" workspace first.</p>
      </section>

      <hr class="rule" />

      <section class="checklist">
        <div class="caption list-caption">Capabilities</div>
        <div class="grid">
          {#each shownCapabilities(draft.capabilities) as id (id)}
            {@render check(
              draft.capabilities[id],
              label(id),
              () => (draft.capabilities[id] = !draft.capabilities[id]),
            )}
          {/each}
        </div>
      </section>

      {#if features.length}
        <section class="checklist">
          <div class="caption list-caption">Default Features</div>
          <div class="grid">
            {#each features as id (id)}
              {@render check(draft.defaultFeatures.includes(id), label(id), () =>
                toggleFeature(id),
              )}
            {/each}
          </div>
        </section>
      {/if}

      {#if draft.capabilities.builtin_tools}
        <section class="checklist">
          <div class="caption list-caption">Builtin Tools</div>
          <div class="grid">
            {#each BUILTIN_TOOLS as [id, name] (id)}
              {@render check(
                draft.builtinTools[id],
                name,
                () => (draft.builtinTools[id] = !draft.builtinTools[id]),
              )}
            {/each}
          </div>
        </section>
      {/if}

      <hr class="rule" />

      {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
      <div class="save-row">
        <button class="save" type="submit" disabled={saving}>
          <span>Save & Create</span>
          {#if saving}<Wire />{/if}
        </button>
      </div>

      <div class="json">
        <div class="json-head">
          <span>JSON Preview</span>
          <button type="button" class="json-toggle" onclick={() => (json = !json)}
            ><span>{json ? 'Hide' : 'Show'}</span></button
          >
        </div>
        {#if json}
          <textarea class="json-text" rows="10" readonly value={preview} aria-label="JSON Preview"
          ></textarea>
        {/if}
      </div>
    </form>
  </div>
</div>

<style>
  .frame {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-block-size: 0;
    inline-size: 100%;
    padding-inline: 12px;
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

  :global([data-theme='dark']) .back:hover {
    color: var(--color-gray-300);
  }

  .scroll {
    flex: 1;
    min-block-size: 0;
    padding-inline-end: 4px;
    overflow-y: auto;
  }

  form {
    padding-inline: 4px;
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
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) :is(input, textarea)::placeholder {
    color: var(--color-gray-700);
  }

  textarea {
    display: block;
    inline-size: 100%;
    resize: none;
    field-sizing: content;
  }

  .identity {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .head {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-block: 2px;
  }

  .avatar {
    flex-shrink: 0;
    inline-size: 56px;
    block-size: 56px;
    overflow: hidden;
    border-radius: 12px;
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--color-gray-200) 70%, transparent);
    transition: box-shadow 150ms;
  }

  .avatar:hover {
    box-shadow: 0 0 0 1px var(--color-gray-300);
  }

  :global([data-theme='dark']) .avatar {
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--color-white) 10%, transparent);
  }

  :global([data-theme='dark']) .avatar:hover {
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--color-white) 20%, transparent);
  }

  /* The default picture: the white brand-kit mark on its tile, as the running app draws it. */
  .tile {
    display: grid;
    place-items: center;
    inline-size: 100%;
    block-size: 100%;
    background-color: var(--color-mark-tile);
  }

  .tile img {
    inline-size: 44px;
    block-size: 44px;
  }

  .names {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
  }

  .name-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .name {
    flex: 1;
    min-inline-size: 0;
    color: var(--color-gray-900);
    font-size: 18px;
    line-height: 22.5px;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-white);
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

  :global([data-theme='dark']) .access:hover {
    background-color: var(--color-gray-800);
  }

  .id {
    inline-size: 100%;
    padding-block: 2px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .caption,
  .sub-caption,
  .toggle,
  .title,
  .help {
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .caption {
    color: var(--color-gray-400);
  }

  .sub-caption {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .caption {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .sub-caption {
    color: var(--color-gray-400);
  }

  .caption-row {
    display: flex;
    justify-content: space-between;
    margin-block-end: 4px;
  }

  .toggle {
    color: var(--color-gray-500);
    transition: color 150ms;
  }

  .toggle:hover {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .toggle:hover {
    color: var(--color-gray-300);
  }

  /* The picker's line sits 6 px under the caption's 4 px gap, as the running app measures. */
  .base {
    block-size: 24px;
    margin-block-start: 4px;
    padding-block-start: 6px;
  }

  :global(.base-trigger) {
    display: flex;
    align-items: center;
    inline-size: 100%;
    padding-inline: 2px;
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    line-height: 16px;
    text-align: start;
  }

  :global(.base-trigger > :first-child) {
    flex: 1;
  }

  :global(.base-trigger > svg) {
    margin-inline-start: 4px;
    color: var(--color-gray-400);
    transition: rotate 300ms;
  }

  :global(.base-trigger[data-state='open'] > svg) {
    rotate: 180deg;
  }

  :global([data-theme='dark'] .base-trigger) {
    color: var(--color-gray-100);
  }

  :global(.base-panel) {
    z-index: 9999;
    inline-size: min(320px, calc(100vw - 16px));
    padding: 4px;
    border: 1px solid var(--color-gray-100);
    border-radius: 16px;
    background-color: var(--color-white);
    box-shadow:
      0 1px 2px -1px rgb(16 24 40 / 0.06),
      0 16px 40px -16px rgb(16 24 40 / 0.22);
  }

  :global([data-theme='dark'] .base-panel) {
    border-color: var(--color-gray-800);
    background-color: var(--color-gray-850);
  }

  .base-search {
    display: flex;
    align-items: center;
    gap: 8px;
    block-size: 27px;
    margin: 2px 2px 2px 8px;
    font-size: var(--text-small);
  }

  .base-search input {
    inline-size: 100%;
  }

  .base-search input::placeholder {
    color: var(--color-gray-400);
  }

  .base-list {
    display: flex;
    flex-direction: column;
    max-block-size: 288px;
    overflow-y: auto;
  }

  .base-row {
    display: flex;
    align-items: center;
    gap: 8px;
    block-size: 50px;
    padding-inline: 10px;
    border-radius: 10px;
    color: var(--color-gray-700);
    font-size: var(--text-small);
    text-align: start;
    transition: background-color 75ms;
  }

  .base-row:hover {
    background-color: var(--color-gray-50);
  }

  .base-row[aria-selected='true'] {
    background-color: color-mix(in srgb, var(--color-gray-50) 70%, transparent);
  }

  :global([data-theme='dark']) .base-row {
    color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .base-row:hover {
    background-color: color-mix(in srgb, var(--color-white) 5%, transparent);
  }

  .base-mark {
    inline-size: 16px;
    block-size: 16px;
    padding: 2px;
    border-radius: var(--radius-pill);
    background-color: var(--color-mark-tile);
  }

  .base-empty {
    padding: 8px 10px;
    font-size: var(--text-small);
  }

  .description {
    min-block-size: 32px;
    padding-block: 4px;
    color: var(--color-gray-700);
    font-size: var(--text-small);
    line-height: 19.5px;
  }

  :global([data-theme='dark']) .description {
    color: var(--color-gray-300);
  }

  .tags {
    padding-block-start: 12px;
  }

  .params {
    margin-block-start: 12px;
  }

  .params-caption {
    margin-block-end: 8px;
  }

  .params > .sub-caption {
    display: block;
    margin-block-end: 4px;
  }

  .system {
    min-block-size: 48px;
    padding-block: 4px;
    color: var(--color-gray-700);
    font-size: var(--text-small);
    line-height: 19.5px;
  }

  :global([data-theme='dark']) .system {
    color: var(--color-gray-300);
  }

  .advanced {
    display: flex;
    align-items: center;
    justify-content: space-between;
    block-size: 28px;
    margin-block-start: 16px;
  }

  .rule {
    margin-block: 12px;
    border: 0;
    border-block-start: 1px solid color-mix(in srgb, var(--color-gray-100) 30%, transparent);
  }

  .rule.first {
    margin-block: 8px 10px;
  }

  :global([data-theme='dark']) .rule {
    border-color: color-mix(in srgb, var(--color-gray-850) 30%, transparent);
  }

  .prompts {
    margin-block-end: 12px;
  }

  .prompts .caption-row {
    margin-block-end: 0;
  }

  .suggestions {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-block: 8px;
  }

  .suggestions-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    block-size: 24px;
    margin-block-end: 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .add,
  .remove {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    color: var(--color-gray-500);
    transition: color 150ms;
  }

  .add:hover {
    color: var(--color-gray-700);
  }

  .suggestion {
    display: flex;
    gap: 4px;
    padding: 4px 8px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 40%, transparent);
    border-radius: 8px;
  }

  :global([data-theme='dark']) .suggestion {
    border-color: color-mix(in srgb, var(--color-gray-850) 50%, transparent);
  }

  .suggestion-fields {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 2px;
  }

  .suggestion-titles {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }

  .suggestion :is(input, textarea) {
    color: var(--color-gray-700);
    font-size: var(--text-small);
    line-height: 20px;
  }

  .suggestion .subtitle {
    color: var(--color-gray-500);
  }

  .remove {
    color: color-mix(in srgb, var(--color-gray-400) 70%, transparent);
  }

  .remove:hover {
    color: var(--color-gray-700);
  }

  .none {
    margin-block-end: 6px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  .block {
    margin-block: 12px;
  }

  .block-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-block-end: 4px;
  }

  .title {
    color: var(--color-gray-500);
  }

  .link {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .link:hover {
    text-decoration: underline;
  }

  :global([data-theme='dark']) .link {
    color: var(--color-gray-400);
  }

  /* The running app sets help 12 px under its heading, 8 px under Skills. */
  .help {
    margin-block-start: 12px;
    color: var(--color-gray-700);
  }

  .help.tight {
    margin-block-start: 8px;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-block-end: 10px;
  }

  .chip {
    display: flex;
    align-items: center;
    gap: 6px;
    max-inline-size: 224px;
    padding: 2px 8px 2px 0;
    color: var(--color-gray-700);
    font-size: var(--text-caption);
  }

  .knowledge-row {
    display: flex;
    align-items: center;
    gap: 4px;
    min-block-size: 27px;
    padding-inline: 8px;
    border-radius: 12px;
    font-size: var(--text-small);
  }

  .knowledge-row:hover {
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
  }

  :global(.knowledge-panel) {
    inline-size: 256px;
  }

  .none-found {
    padding: 16px 0 24px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  .picked {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 12px;
    margin-block-start: 4px;
  }

  .clear-all {
    padding-block: 2px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .clear-all:hover {
    color: var(--color-gray-700);
  }

  .checklist + .checklist {
    margin-block-start: 12px;
  }

  .list-caption {
    margin-block-end: 6px;
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 4px 20px;
  }

  @media (width >= 640px) {
    .grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (width >= 1024px) {
    .grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  .item {
    display: flex;
    align-items: center;
    gap: 10px;
    min-block-size: 24px;
  }

  .box {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 14px;
    block-size: 14px;
    border-radius: 4px;
    outline: 1.5px solid var(--color-gray-200);
    outline-offset: -1px;
    color: var(--color-white);
  }

  .box:hover:not([data-checked]) {
    background-color: var(--color-gray-50);
    outline-color: var(--color-gray-500);
  }

  /* Checked keeps the grey outline: in the running app its grey class wins over the black one. */
  .box[data-checked] {
    background-color: var(--color-black);
  }

  :global([data-theme='dark']) .box {
    outline-color: var(--color-gray-600);
  }

  .item-label {
    overflow: hidden;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    line-height: 16px;
    text-align: start;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :global([data-theme='dark']) .item-label {
    color: var(--color-gray-400);
  }

  .problem {
    margin-block-end: 8px;
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }

  .save-row {
    display: flex;
    justify-content: flex-end;
    margin-block: 8px;
  }

  .save {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    inline-size: 100%;
    padding: 8px 12px;
    border-radius: 8px;
    background-color: var(--color-black);
    color: var(--color-white);
    font-size: var(--text-ui);
    line-height: 20px;
    transition: background-color 150ms;
  }

  .save:hover {
    background-color: var(--color-gray-900);
  }

  .save:disabled {
    cursor: not-allowed;
  }

  :global([data-theme='dark']) .save {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :global([data-theme='dark']) .save:hover {
    background-color: var(--color-gray-100);
  }

  .json {
    margin-block: 8px;
    padding-block-end: 80px;
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .json {
    color: var(--color-gray-700);
  }

  .json-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: 8px;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .json-toggle {
    padding: 4px 12px;
    border-radius: 4px;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .json-toggle span {
    margin-inline-start: 8px;
  }

  .json-text {
    font-size: var(--text-ui);
    line-height: 20px;
  }

  :is(button, a):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
