<script lang="ts">
  // A workspace tab's screen (workspace look §2): Models is built; the other tabs follow one at a
  // time. The tab row and Create sit in the workspace layout.
  import { m } from '$lib/i18n/generated/messages.js';
  import { goto, invalidateAll } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { data as source } from '$lib/data';
  import CreatePromptDialog from '$lib/ui/components/CreatePromptDialog.svelte';
  import KnowledgeList from '$lib/ui/components/KnowledgeList.svelte';
  import PromptList from '$lib/ui/components/PromptList.svelte';
  import SkillList from '$lib/ui/components/SkillList.svelte';
  import { saveSkillFile } from '$lib/ui/skills';
  import { cloneDraft, savePromptFile, type PromptDraft } from '$lib/ui/prompts';
  import Menu from '$lib/ui/components/Menu.svelte';
  import ModelRow from '$lib/ui/components/ModelRow.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  // A clone opens the create dialog with the copy filled in (F92).
  let cloning = $state<PromptDraft>();

  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  const VIEWS = { all: 'All', mine: 'Created by you', shared: 'Shared with you' } as const;
  const models = $derived(
    data.models.filter((model) => model.name.toLowerCase().includes(query.trim().toLowerCase())),
  );
</script>

<svelte:head><title>Workspace / {m.app_name()}</title></svelte:head>

{#if data.tab === 'models'}
  <div class="screen">
    <div class="toolbar">
      <label class="search">
        <span class="search-icon"><Icon name="magnifying-glass" size={14} /></span>
        <input
          bind:value={query}
          placeholder="Search Models"
          maxlength="500"
          aria-label="Search Models"
        />
        {#if query}
          <button
            type="button"
            class="clear"
            aria-label="Clear search"
            onclick={() => (query = '')}
          >
            <Icon name="tools-failed" size={12} />
          </button>
        {/if}
      </label>
      <div class="filters">
        <Menu
          label={VIEWS[view]}
          backLabel="Back"
          align="end"
          items={[
            {
              type: 'choices',
              id: 'view',
              label: 'View',
              value: view,
              options: [
                { value: 'all', label: VIEWS.all },
                { value: 'mine', label: VIEWS.mine },
                { value: 'shared', label: VIEWS.shared },
              ],
              onChange: (value) => (view = value as typeof view),
            },
          ]}
        >
          {#snippet trigger({ props })}
            <button {...props} class="filter"
              ><span class="view-label">{VIEWS[view]}</span><Icon
                name="caret-down"
                size={9}
              /></button
            >
          {/snippet}
        </Menu>
        <Menu
          label="Actions"
          backLabel="Back"
          align="end"
          items={[
            { id: 'enable', label: 'Enable All', icon: 'mark-unread' },
            { id: 'disable', label: 'Disable All', icon: 'minus' },
            { type: 'separator' },
            { id: 'show', label: 'Show All', icon: 'eye' },
            { id: 'hide', label: 'Hide All', icon: 'eye-slash' },
          ]}
        >
          {#snippet trigger({ props })}
            <button {...props} class="filter actions" title="Actions"
              >Actions<Icon name="caret-down" size={12} /></button
            >
          {/snippet}
        </Menu>
      </div>
    </div>

    {#if models.length}
      <div class="rows">
        {#each models as model (model.id)}<ModelRow {model} />{/each}
      </div>
    {:else}
      <div class="empty">
        <div class="empty-inner">
          <p class="empty-title">No models found</p>
          <p class="empty-help">
            Try adjusting your search or filter to find what you are looking for.
          </p>
        </div>
      </div>
    {/if}
  </div>
{:else if data.tab === 'knowledge'}
  <KnowledgeList
    bases={data.bases}
    me={data.user?.email}
    admin={data.user?.role === 'admin'}
    onopen={(id) => goto(resolve('/workspace/[tab]/[id]', { tab: 'knowledge', id }))}
    ondelete={async (id) => {
      await source.deleteKnowledge(id);
      await invalidateAll();
    }}
  />
{:else if data.tab === 'prompts'}
  <PromptList
    prompts={data.prompts}
    me={data.user?.email}
    onopen={(id) => goto(resolve('/workspace/[tab]/[id]', { tab: 'prompts', id }))}
    ontoggle={async (id, active) => {
      await source.setPromptActive(id, active);
      await invalidateAll();
    }}
    onclone={(prompt) => (cloning = cloneDraft(prompt))}
    onexport={(prompt) => savePromptFile([prompt])}
    ondelete={async (id) => {
      await source.deletePrompt(id);
      await invalidateAll();
    }}
  />
  {#if cloning}
    <CreatePromptDialog
      open
      prefill={cloning}
      onclose={() => (cloning = undefined)}
      oncreate={async (draft) => {
        await source.createPrompt(draft);
        cloning = undefined;
        await invalidateAll();
      }}
    />
  {/if}
{:else if data.tab === 'skills'}
  <SkillList
    skills={data.skills}
    me={data.user?.email}
    onopen={(id) => goto(resolve('/workspace/[tab]/[id]', { tab: 'skills', id }))}
    ontoggle={async (id, active) => {
      await source.setSkillActive(id, active);
      await invalidateAll();
    }}
    onclone={(skill) =>
      goto(resolve('/workspace/[tab]/create', { tab: 'skills' }), {
        state: {
          skillDraft: {
            id: `${skill.id}_clone`,
            name: `${skill.name} (Clone)`,
            description: skill.description ?? '',
            instructions: skill.instructions,
          },
        },
      })}
    onexport={(skill) => saveSkillFile([skill], skill.id)}
    ondelete={async (id) => {
      await source.deleteSkill(id);
      await invalidateAll();
    }}
  />
{/if}

<style>
  .screen {
    display: flex;
    flex-direction: column;
    gap: 4px;
    /* 12 px each side, measured against the running app. */
    padding-inline: 12px;
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    block-size: 32px;
  }

  .search {
    display: flex;
    flex: 1;
    align-items: center;
    min-inline-size: 0;
    color: var(--color-gray-700);
  }

  .search-icon {
    display: inline-flex;
    margin-inline: 4px 12px;
  }

  .search input {
    inline-size: 100%;
    padding-block: 4px;
    border-radius: 0 12px 12px 0;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .search input::placeholder {
    color: var(--color-gray-400);
  }

  .search input:focus {
    outline: none;
  }

  .clear {
    display: grid;
    place-items: center;
    margin-inline-start: 6px;
    padding: 2px;
    border-radius: var(--radius-pill);
  }

  .clear:hover {
    background-color: var(--color-gray-100);
  }

  .filters {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 4px;
    max-inline-size: 60%;
    overflow-x: auto;
    scrollbar-width: none;
  }

  /* The running app's label box is 5 px wider than its text, which sets the caret apart. */
  .view-label {
    padding-inline-end: 5px;
  }

  .filter {
    display: flex;
    align-items: center;
    gap: 2px;
    block-size: 32px;
    padding: 6px;
    border-radius: var(--radius-inset);
    color: var(--color-gray-700);
    font-size: var(--text-small);
    transition: color 150ms;
  }

  .filter.actions {
    gap: 6px;
    max-inline-size: 112px;
  }

  .filter:hover {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) :is(.search, .filter) {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .filter:hover {
    color: var(--color-gray-100);
  }

  .rows {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-block-start: 4px;
  }

  /* Empty (look §2.4): 64 px above, 96 below, a 384 px centred block. */
  .empty {
    display: flex;
    justify-content: center;
    padding: 64px 0 96px;
  }

  .empty-inner {
    max-inline-size: 384px;
    color: var(--color-gray-900);
    text-align: center;
  }

  :global([data-theme='dark']) .empty-inner {
    color: var(--color-gray-100);
  }

  .empty-title {
    margin-block-end: 6px;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .empty-help {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 20px;
  }

  :is(.filter, .clear):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
