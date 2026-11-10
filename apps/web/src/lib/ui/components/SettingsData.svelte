<script lang="ts">
  // Data Controls (chat-composer look §9.11, F100): import and export chats as JSON, archive or
  // delete them all after confirmation. Shared Chats and Manage Files open their own dialogs,
  // which come later, as the owner chose; their rows are shown but Manage is not yet live.
  import type { Chat, DataSource } from '$lib/data';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import './settings-page.css';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  let picker = $state<HTMLInputElement>();
  let notice = $state('');
  let confirming = $state<'archive' | 'delete'>();

  type Imported = Pick<Chat, 'title' | 'messages'>;

  /** Reads an export: a list of chats, each either bare or wrapped as { chat }. */
  function readExport(text: string): Imported[] | undefined {
    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      return undefined;
    }
    if (!Array.isArray(data)) return undefined;
    const chats: Imported[] = [];
    for (const item of data as unknown[]) {
      const record = (item as { chat?: unknown })?.chat ?? item;
      const { title, messages } = (record ?? {}) as { title?: unknown; messages?: unknown };
      if (typeof title !== 'string') return undefined;
      chats.push({
        title,
        messages: Array.isArray(messages) ? (messages as Chat['messages']) : [],
      });
    }
    return chats;
  }

  async function importFile(event: Event & { currentTarget: HTMLInputElement }) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    const chats = readExport(await file.text());
    if (!chats) {
      notice = 'That file is not a chat export.';
      return;
    }
    const added = await source.importChats(chats);
    notice = `Imported ${added} ${added === 1 ? 'chat' : 'chats'}.`;
  }

  async function exportChats() {
    const blob = new Blob([JSON.stringify(await source.exportChats())], {
      type: 'application/json',
    });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `chat-export-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  async function confirm() {
    if (confirming === 'archive') await source.archiveAllChats();
    else await source.deleteAllChats();
    confirming = undefined;
  }
</script>

{#snippet row(label: string, note: string, action: string, onclick?: () => void)}
  <div class="block">
    <div class="row tall">
      <span>{label}</span>
      <button type="button" class="quiet" disabled={!onclick} {onclick}>{action}</button>
    </div>
    <p class="note">{note}</p>
  </div>
{/snippet}

<div class="settings-page">
  <h2>Data Controls</h2>
  <input
    bind:this={picker}
    type="file"
    accept=".json"
    hidden
    aria-label="Chat export file"
    onchange={importFile}
  />
  <div class="body">
    <section>
      <h3>Chats</h3>
      <div class="rows">
        {@render row('Import Chats', 'Import chat history from a JSON export file.', 'Import', () =>
          picker?.click(),
        )}
        {@render row(
          'Export Chats',
          'Download your chat history as a JSON export.',
          'Export',
          exportChats,
        )}
        {@render row('Shared Chats', 'Review and manage chats you have shared.', 'Manage')}
        {@render row(
          'Archive All Chats',
          'Move every chat into the archive after confirmation.',
          'Archive All',
          () => (confirming = 'archive'),
        )}
        {@render row(
          'Delete All Chats',
          'Permanently delete every chat after confirmation.',
          'Delete All',
          () => (confirming = 'delete'),
        )}
      </div>
      <p class="notice" role="status">{notice}</p>
    </section>
    <section>
      <h3>Files</h3>
      <div class="rows">
        {@render row('Manage Files', 'Open the file manager for uploaded files.', 'Manage')}
      </div>
    </section>
  </div>
</div>

<ConfirmDialog
  open={confirming !== undefined}
  title={confirming === 'archive' ? 'Archive All Chats' : 'Delete All Chats'}
  message={`Are you sure you want to ${confirming === 'archive' ? 'archive' : 'delete'} all chats? This action cannot be undone.`}
  onconfirm={confirm}
  oncancel={() => (confirming = undefined)}
/>

<style>
  .notice:not(:empty) {
    margin-block-start: 10px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  /* The running app draws the actions 1 px below the row's centre. */
  .quiet {
    padding-block-start: 2px;
  }

  .quiet:disabled {
    cursor: default;
  }

  .quiet:disabled:hover {
    color: var(--color-gray-500);
  }
</style>
