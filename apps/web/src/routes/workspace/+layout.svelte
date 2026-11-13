<script lang="ts">
  // The workspace frame (workspace look §1): the tab row on every workspace screen, and the Create
  // control on the tab lists. The current tab is the first part of the path.
  import { goto, invalidateAll } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { page } from '$app/state';
  import type { WorkspaceTab } from '$lib/data';
  import { data as source } from '$lib/data';
  import ConfirmDialog from '$lib/ui/components/ConfirmDialog.svelte';
  import Menu from '$lib/ui/components/Menu.svelte';
  import RiskNotice from '$lib/ui/components/RiskNotice.svelte';
  import WorkspaceTabs from '$lib/ui/components/WorkspaceTabs.svelte';
  import { readPromptFile, savePromptFile } from '$lib/ui/prompts';
  import { readSkillFile, saveSkillFile } from '$lib/ui/skills';
  import { readToolFile, saveToolFile, type ToolDraft } from '$lib/ui/tools';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import type { LayoutProps } from './$types';

  let { children, data }: LayoutProps = $props();

  let importInput = $state<HTMLInputElement>();
  let skillInput = $state<HTMLInputElement>();
  let toolInput = $state<HTMLInputElement>();
  let pendingTools = $state<ToolDraft[]>();

  const current = $derived((page.url.pathname.split('/')[2] ?? 'models') as WorkspaceTab);
  // The tab lists, and the Knowledge create page, which is the list with its dialog open.
  const list = $derived(
    page.route.id === '/workspace/[tab]' ||
      (page.route.id === '/workspace/[tab]/create' &&
        (current === 'knowledge' || current === 'prompts')),
  );
</script>

<div class="workspace">
  <header class="bar" data-page-bar>
    <WorkspaceTabs {current} counts={data.counts} />
    {#if list}
      <span class="create">
        {#if current === 'models'}
          <a class="create-main" href={resolve('/workspace/[tab]/create', { tab: 'models' })}
            >Create</a
          >
          <button type="button" class="create-more" aria-label="Open create menu">
            <Icon name="caret-down" size={10} />
          </button>
        {:else if current === 'knowledge'}
          <!-- Knowledge has one way to create (look §4.1), so no menu. -->
          <a class="create-main" href={resolve('/workspace/[tab]/create', { tab: 'knowledge' })}
            >Create</a
          >
        {:else if current === 'prompts'}
          <a class="create-main" href={resolve('/workspace/[tab]/create', { tab: 'prompts' })}
            >Create</a
          >
          <Menu
            label="Open create menu"
            backLabel="Back"
            align="end"
            items={[
              {
                id: 'import',
                label: 'Import from JSON',
                icon: 'upload-simple',
                onSelect: () => importInput?.click(),
              },
              {
                id: 'export',
                label: 'Export as JSON',
                icon: 'download-simple',
                onSelect: async () => savePromptFile(await source.listPrompts()),
              },
            ]}
          >
            {#snippet trigger({ props })}
              <button {...props} class="create-more" aria-label="Open create menu"
                ><Icon name="caret-down" size={10} /></button
              >
            {/snippet}
          </Menu>
          <input
            bind:this={importInput}
            type="file"
            accept=".json"
            hidden
            onchange={async (event) => {
              const file = event.currentTarget.files?.[0];
              event.currentTarget.value = '';
              if (!file) return;
              // Each entry is created on its own; one failing does not stop the rest (F92).
              for (const draft of readPromptFile(await file.text())) {
                await source.createPrompt(draft).catch(() => undefined);
              }
              await invalidateAll();
            }}
          />
        {:else if current === 'skills'}
          <a class="create-main" href={resolve('/workspace/[tab]/create', { tab: 'skills' })}
            >Create</a
          >
          <Menu
            label="Open create menu"
            backLabel="Back"
            align="end"
            items={[
              {
                id: 'import',
                label: 'Import from file',
                icon: 'upload-simple',
                onSelect: () => skillInput?.click(),
              },
              {
                id: 'export',
                label: 'Export as JSON',
                icon: 'download-simple',
                onSelect: async () => saveSkillFile(await source.listSkills()),
              },
            ]}
          >
            {#snippet trigger({ props })}
              <button {...props} class="create-more" aria-label="Open create menu"
                ><Icon name="caret-down" size={10} /></button
              >
            {/snippet}
          </Menu>
          <input
            bind:this={skillInput}
            type="file"
            accept=".md,.json"
            hidden
            onchange={async (event) => {
              const file = event.currentTarget.files?.[0];
              event.currentTarget.value = '';
              if (!file) return;
              const drafts = readSkillFile(file.name, await file.text());
              // A Markdown skill opens in the editor to check; JSON entries are created as they
              // are, one failing not stopping the rest (F104).
              if (!file.name.toLowerCase().endsWith('.json')) {
                await goto(resolve('/workspace/[tab]/create', { tab: 'skills' }), {
                  state: { skillDraft: drafts[0] },
                });
                return;
              }
              for (const draft of drafts) await source.createSkill(draft).catch(() => undefined);
              await invalidateAll();
            }}
          />
        {:else if current === 'tools'}
          <a class="create-main" href={resolve('/workspace/[tab]/create', { tab: 'tools' })}
            >Create</a
          >
          <Menu
            label="Open create menu"
            backLabel="Back"
            align="end"
            items={[
              {
                id: 'import',
                label: 'Import from JSON',
                icon: 'upload-simple',
                onSelect: () => toolInput?.click(),
              },
              {
                id: 'export',
                label: 'Export as JSON',
                icon: 'download-simple',
                onSelect: async () => saveToolFile(await source.listTools()),
              },
            ]}
          >
            {#snippet trigger({ props })}
              <button {...props} class="create-more" aria-label="Open create menu"
                ><Icon name="caret-down" size={10} /></button
              >
            {/snippet}
          </Menu>
          <input
            bind:this={toolInput}
            type="file"
            accept=".json"
            hidden
            onchange={async (event) => {
              const file = event.currentTarget.files?.[0];
              event.currentTarget.value = '';
              if (file) pendingTools = readToolFile(await file.text());
            }}
          />
        {:else}
          <button type="button" class="create-main">Create</button>
        {/if}
      </span>
    {/if}
  </header>
  {@render children()}
</div>

<!-- Imported tools run code, so the person accepts the risk first (F112). -->
<ConfirmDialog
  open={pendingTools !== undefined}
  message=""
  oncancel={() => (pendingTools = undefined)}
  onconfirm={async () => {
    const drafts = pendingTools ?? [];
    pendingTools = undefined;
    for (const draft of drafts) await source.createTool(draft).catch(() => undefined);
    await invalidateAll();
  }}
>
  <RiskNotice />
</ConfirmDialog>

<style>
  .workspace {
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
    block-size: 100%;
  }

  /* The bar (workspace look §1.2): 8 px top, 10 px sides, 4 px bottom; blurred, no fill. */
  .bar {
    display: flex;
    align-items: center;
    padding: var(--spacing-2) 10px 4px;
    backdrop-filter: blur(24px);
    user-select: none;
  }

  /* Create (look §1.3): one joined box; the chevron opens the create menu. */
  .create {
    display: flex;
    flex-shrink: 0;
    margin-inline-start: auto;
    overflow: hidden;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    color: var(--color-gray-900);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .create-main,
  .create-more {
    padding: 4px 10px;
    transition: background-color 150ms;
  }

  .create-more {
    display: grid;
    place-items: center;
    padding-inline: 6px;
    border-inline-start: 1px solid var(--color-gray-200);
  }

  :is(.create-main, .create-more):hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .create {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
    color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .create-more {
    border-color: var(--color-gray-800);
  }

  :global([data-theme='dark']) :is(.create-main, .create-more):hover {
    background-color: var(--color-gray-800);
  }

  :is(.create-main, .create-more):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
