<script lang="ts">
  // The admin settings content (admin look §18 to §32): the chosen panel, Default Group's groups,
  // and the Database actions, each behind a typed confirmation. A config import can be undone
  // straight after; every action is logged by the data source.
  import type { DataSource } from '$lib/data';
  import { PANELS, type PanelId } from '$lib/ui/admin-panels';
  import AdminPanel from './AdminPanel.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';

  type Props = { source: DataSource; panel: PanelId };

  let { source, panel }: Props = $props();

  type Action =
    | 'import-config'
    | 'export-config'
    | 'export-database'
    | 'export-chats'
    | 'export-users'
    | 'reset-uploads'
    | 'reset-vectors'
    | 'reindex';
  let groups = $state<[string, string][]>([]);
  let models = $state<[string, string][]>([]);
  let pending = $state<Action>();
  let typed = $state('');
  let notice = $state('');
  let undo = $state<Record<string, Record<string, unknown>>>();
  let picker = $state<HTMLInputElement>();

  $effect(() => {
    void source.listGroups().then((all) => (groups = all.map((one) => [one.id, one.name])));
    void source.listBaseModels().then((all) => (models = all.map((one) => [one.id, one.name])));
  });

  const resets = (action?: Action) => action === 'reset-uploads' || action === 'reset-vectors';
  const WORD = $derived(
    pending === 'import-config'
      ? 'IMPORT'
      : resets(pending)
        ? 'RESET'
        : pending === 'reindex'
          ? 'REINDEX'
          : 'EXPORT',
  );

  function download(text: string, name: string, type: string) {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([text], { type }));
    link.download = name;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  async function run() {
    const action = pending;
    pending = undefined;
    typed = '';
    notice = '';
    if (action === 'import-config') {
      picker?.click();
      return;
    }
    if (action === 'reset-uploads' || action === 'reset-vectors' || action === 'reindex') {
      await source.adminMaintenance(action);
      notice = action === 'reindex' ? 'Reindexing has started.' : 'Done. This cannot be undone.';
      return;
    }
    const kind = action?.replace('export-', '') as 'config' | 'chats' | 'users' | 'database';
    const text = await source.exportAdminData(kind);
    if (text === undefined) {
      notice = 'This server cannot export its database file.';
      return;
    }
    const stamp = Date.now();
    if (kind === 'users') download(text, `users-${stamp}.csv`, 'text/csv');
    else download(text, `${kind}-export-${stamp}.json`, 'application/json');
  }

  async function importFile(event: Event & { currentTarget: HTMLInputElement }) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    let config: unknown;
    try {
      config = JSON.parse(await file.text());
    } catch {
      notice = 'That file is not an admin config export.';
      return;
    }
    if (!config || typeof config !== 'object' || Array.isArray(config)) {
      notice = 'That file is not an admin config export.';
      return;
    }
    undo = await source.importAdminConfig(config as Record<string, Record<string, unknown>>);
    notice = 'Config imported successfully';
  }
</script>

{#key panel}
  <AdminPanel
    {source}
    panel={PANELS[panel]}
    choices={{
      DEFAULT_GROUP_ID: groups,
      TASK_MODEL: models,
      TASK_MODEL_EXTERNAL: models,
      CONTEXT_COMPACTION_MODEL: models,
    }}
    onaction={(key) => (pending = key as Action)}
  />
{/key}
<input
  bind:this={picker}
  type="file"
  accept=".json"
  hidden
  aria-label="Config file"
  onchange={importFile}
/>
{#if notice}
  <p class="notice" role="status">
    {notice}
    {#if undo}
      <button
        type="button"
        onclick={async () => {
          if (undo) await source.importAdminConfig(undo);
          undo = undefined;
          notice = 'Import undone.';
        }}>Undo</button
      >
    {/if}
  </p>
{/if}

<ConfirmDialog
  open={pending !== undefined}
  title={pending === 'import-config'
    ? 'Import config?'
    : resets(pending)
      ? 'Reset?'
      : pending === 'reindex'
        ? 'Reindex?'
        : 'Export data?'}
  message={pending === 'import-config'
    ? `This replaces every admin setting. Type ${WORD} to confirm.`
    : resets(pending)
      ? `This permanently deletes the data and cannot be undone. Type ${WORD} to confirm.`
      : pending === 'reindex'
        ? `This rebuilds every vector and may take a while. Type ${WORD} to confirm.`
        : `This downloads sensitive data. Type ${WORD} to confirm.`}
  confirmLabel={pending === 'import-config'
    ? 'Import'
    : resets(pending)
      ? 'Reset'
      : pending === 'reindex'
        ? 'Reindex'
        : 'Export'}
  confirmDisabled={typed.trim() !== WORD}
  onconfirm={run}
  oncancel={() => {
    pending = undefined;
    typed = '';
  }}
>
  <input class="typed" bind:value={typed} placeholder={WORD} aria-label="Confirmation" />
</ConfirmDialog>

<style>
  .notice {
    display: flex;
    gap: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .notice button {
    color: inherit;
    text-decoration: underline;
  }

  .typed {
    inline-size: 100%;
    margin-block-start: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    font-size: var(--text-ui);
  }

  :global([data-theme='dark']) .typed {
    background-color: var(--color-gray-900);
    color: var(--color-gray-300);
  }
</style>
