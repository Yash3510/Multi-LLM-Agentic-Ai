<script lang="ts">
  // A file a run produced or a person added (web-screens.md, file card): the kind's file icon and a
  // neutral type tag, the name, size, hash prefix and classification, and its state until it is
  // ready. Opening or downloading waits for files from the server.
  import type { FileInfo } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { fileSize } from '$lib/ui/knowledge';

  let { file }: { file: FileInfo } = $props();

  const ICONS: Record<string, 'file-doc' | 'file-xls' | 'file-ppt'> = {
    docx: 'file-doc',
    xlsx: 'file-xls',
    pptx: 'file-ppt',
  };
  const STATES: Record<FileInfo['state'], string> = {
    uploading: 'Uploading…',
    scanning: 'Scanning…',
    parsing: 'Reading…',
    ready: '',
    failed: 'Failed',
  };
</script>

<div class="file-card" data-state={file.state}>
  <Icon name={ICONS[file.kind] ?? 'file'} size={20} />
  <div class="text">
    <span class="name">{file.name}</span>
    <span class="meta">
      <span class="tag">{file.kind.toUpperCase()}</span>
      {fileSize(file.size)} · <code>{file.hash.slice(0, 8)}…</code>
      {#if file.classification}· {file.classification}{/if}
      {#if STATES[file.state]}· <span class="state">{STATES[file.state]}</span>{/if}
    </span>
  </div>
</div>

<style>
  /* One outlined box, like the answer's tables and the receipt's labels. */
  .file-card {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-3);
    max-inline-size: 100%;
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-control);
    background-color: var(--color-surface-raised);
    color: var(--color-ink-3);
  }

  .text {
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
  }

  .name {
    overflow: hidden;
    color: var(--color-ink-1);
    font-size: var(--text-small);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .meta {
    font-size: var(--text-caption);
  }

  .tag {
    padding-inline: 4px;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-tight);
    font-family: var(--font-mono);
    font-size: var(--text-tag);
    letter-spacing: 0.06em;
  }

  .file-card[data-state='failed'] .state {
    color: var(--color-stop);
  }
</style>
