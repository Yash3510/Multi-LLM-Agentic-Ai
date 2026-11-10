<script lang="ts">
  // The notes list (notes look §1, F1 to F20): search, view and layout filters, notes grouped by
  // day as rows or cards, and each note's menu (download, delete with Undo).
  import { DropdownMenu } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { DataSource, Note } from '$lib/data';
  import { ago } from '$lib/ui/ago';
  import { timeGroup } from '$lib/ui/format';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import './menu.css';
  import './surfaces.css';

  type Props = {
    source: DataSource;
    selfEmail?: string;
    /** A note just deleted from its editor, offered for Undo. */
    deletedId?: string;
  };

  let { source, selfEmail, deletedId }: Props = $props();

  let notes = $state<Note[]>();
  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  let access = $state<'write' | 'read'>('write');
  let layout = $state<'list' | 'grid'>('list');
  let deleting = $state<Note>();
  let undo = $state<Note>();
  let picker = $state<HTMLInputElement>();

  async function importFiles(event: Event & { currentTarget: HTMLInputElement }) {
    const input = event.currentTarget;
    for (const file of input.files ?? []) {
      await source.createNote({
        title: file.name.replace(/\.(txt|md)$/i, ''),
        content: await file.text(),
      });
    }
    input.value = '';
    await load();
  }

  async function load() {
    notes = await source.listNotes();
  }
  void load();

  // The editor's delete lands here with the note's id; Undo brings it back.
  $effect(() => {
    if (deletedId) undo = { id: deletedId, title: 'the note' } as Note;
  });

  const shown = $derived(
    (notes ?? [])
      .filter((one) =>
        `${one.title} ${one.content}`.toLowerCase().includes(query.trim().toLowerCase()),
      )
      .filter((one) => view === 'all' || (view === 'mine') === (one.owner.email === selfEmail))
      .filter((one) => view === 'mine' || (access === 'read') === Boolean(one.readOnly)),
  );
  const MONTHS = new Intl.DateTimeFormat('en', { month: 'long' });
  function band(note: Note) {
    const group = timeGroup(note.updated);
    if (!group) return '';
    if (group.band === 'today') return 'Today';
    if (group.band === 'yesterday') return 'Yesterday';
    if (group.band === 'week') return 'Previous 7 days';
    if (group.band === 'month') return 'Previous 30 days';
    if (group.band === 'month-name') return MONTHS.format(new Date(2000, group.month, 1));
    return group.band === 'year' ? String(group.year) : '';
  }
  const groups = $derived.by(() => {
    const out: [string, Note[]][] = [];
    for (const note of shown) {
      const label = band(note);
      if (out.at(-1)?.[0] === label) out.at(-1)?.[1].push(note);
      else out.push([label, [note]]);
    }
    return out;
  });

  function download(note: Note, extension: 'md' | 'txt') {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([note.content], { type: 'text/plain' }));
    link.download = `${note.title || 'note'}.${extension}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  async function remove() {
    if (!deleting) return;
    const gone = deleting;
    deleting = undefined;
    await source.deleteNote(gone.id);
    undo = gone;
    await load();
  }

  async function restore() {
    if (!undo) return;
    await source.restoreNote(undo.id);
    undo = undefined;
    await load();
  }

  const href = (note: Note) => resolve('/notes/[id]', { id: note.id });
</script>

{#snippet filter(
  label: string,
  options: [string, string][],
  value: string,
  set: (value: string) => void,
)}
  <DropdownMenu.Root>
    <DropdownMenu.Trigger class="note-filter">
      {options.find(([one]) => one === value)?.[1] ?? label}<Icon
        name="caret-down-bold"
        size={14}
      />
    </DropdownMenu.Trigger>
    <DropdownMenu.Portal>
      <DropdownMenu.Content
        class="note-menu"
        data-menu
        data-surface="float"
        align="end"
        sideOffset={4}
      >
        {#each options as [one, text] (one)}
          <DropdownMenu.Item data-menu-row onSelect={() => set(one)}>
            <span class="grow">{text}</span>
            <span class:hidden={one !== value}><Icon name="check" size={16} /></span>
          </DropdownMenu.Item>
        {/each}
      </DropdownMenu.Content>
    </DropdownMenu.Portal>
  </DropdownMenu.Root>
{/snippet}

{#snippet menu(note: Note)}
  <DropdownMenu.Root>
    <DropdownMenu.Trigger class="note-more" aria-label="Note Menu" title="More">
      <Icon name="dots-three" size={16} />
    </DropdownMenu.Trigger>
    <DropdownMenu.Portal>
      <DropdownMenu.Content
        class="note-menu"
        data-menu
        data-surface="float"
        align="end"
        sideOffset={4}
      >
        <DropdownMenu.Item data-menu-row onSelect={() => download(note, 'md')}>
          <span data-menu-lead><Icon name="download-simple" size={14} /></span>Download .md
        </DropdownMenu.Item>
        <DropdownMenu.Item data-menu-row onSelect={() => download(note, 'txt')}>
          <span data-menu-lead><Icon name="download-simple" size={14} /></span>Download .txt
        </DropdownMenu.Item>
        <DropdownMenu.Separator data-menu-separator />
        <DropdownMenu.Item data-menu-row onSelect={() => (deleting = note)}>
          <span data-menu-lead><Icon name="trash" size={14} /></span>Delete
        </DropdownMenu.Item>
      </DropdownMenu.Content>
    </DropdownMenu.Portal>
  </DropdownMenu.Root>
{/snippet}

<div class="notes">
  <div class="heading">
    <span class="title">Notes <span class="count">{shown.length}</span></span>
    <span class="split">
      <a class="create-main" href={resolve('/notes/create')}>Create</a>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger class="create-more" aria-label="Open create menu"
          ><Icon name="caret-down-bold" size={10} /></DropdownMenu.Trigger
        >
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            class="note-menu"
            data-menu
            data-surface="float"
            align="end"
            sideOffset={6}
          >
            <DropdownMenu.Item data-menu-row>
              {#snippet child({ props })}
                <a {...props} href={resolve('/notes/create')}
                  ><span data-menu-lead><Icon name="rename" size={14} /></span>Create</a
                >
              {/snippet}
            </DropdownMenu.Item>
            <DropdownMenu.Item data-menu-row onSelect={() => picker?.click()}>
              <span data-menu-lead><Icon name="file-arrow-up" size={14} /></span>Import txt/md
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </span>
    <input
      bind:this={picker}
      type="file"
      accept=".txt,.md"
      multiple
      hidden
      aria-label="Note files"
      onchange={importFiles}
    />
  </div>
  <div class="toolbar">
    <label class="search">
      <Icon name="magnifying-glass" size={14} />
      <input bind:value={query} placeholder="Search Notes" aria-label="Search Notes" />
      {#if query}
        <button type="button" class="clear" aria-label="Clear search" onclick={() => (query = '')}
          ><Icon name="x-bold" size={12} /></button
        >
      {/if}
    </label>
    <div class="filters">
      {@render filter(
        'All',
        [
          ['all', 'All'],
          ['mine', 'Created by you'],
          ['shared', 'Shared with you'],
        ],
        view,
        (v) => (view = v as typeof view),
      )}
      {#if view !== 'mine'}
        {@render filter(
          'Write',
          [
            ['write', 'Write'],
            ['read', 'Read Only'],
          ],
          access,
          (v) => (access = v as typeof access),
        )}
      {/if}
      {@render filter(
        'List',
        [
          ['list', 'List'],
          ['grid', 'Grid'],
        ],
        layout,
        (v) => (layout = v as typeof layout),
      )}
    </div>
  </div>
  {#if undo}
    <p class="undo" role="status">
      Deleted {undo.title || 'Untitled'}. <button type="button" onclick={restore}>Undo</button>
    </p>
  {/if}
  {#if notes && !shown.length}
    <div class="empty">
      <p class="empty-title">{notes.length ? 'No results found' : 'No Notes'}</p>
      {#if !notes.length}<p class="empty-hint">Create your first note from the Create menu.</p>{/if}
    </div>
  {:else if notes}
    {#if layout === 'list'}
      <div class="columns">
        <span class="grow">Title</span><span class="owner-space"></span><span class="date-col"
          >Updated at</span
        >
      </div>
    {/if}
    {#each groups as [label, list] (label)}
      <p class="group">{label}</p>
      <div class={layout === 'grid' ? 'grid' : 'rows'}>
        {#each list as note (note.id)}
          {#if layout === 'list'}
            <div class="row">
              <a class="main" href={href(note)}>
                <span class="name">{note.title || 'Untitled'}</span>
                <span class="age">{ago(note.updated)}</span>
              </a>
              <span class="owner" title={note.owner.email}>{note.owner.name}</span>
              {@render menu(note)}
            </div>
          {:else}
            <div class="card">
              <div class="card-top">
                <a class="name grow" href={href(note)}>{note.title || 'Untitled'}</a>
                {@render menu(note)}
              </div>
              <a class="preview" href={href(note)}>{note.content || 'No content'}</a>
              <div class="card-foot">
                <span>{note.owner.name}</span><span>{ago(note.updated)}</span>
              </div>
            </div>
          {/if}
        {/each}
      </div>
    {/each}
  {/if}
</div>

<ConfirmDialog
  open={deleting !== undefined}
  title="Delete note?"
  message="This will delete {deleting?.title || 'Untitled'}. You can undo it straight after."
  onconfirm={remove}
  oncancel={() => (deleting = undefined)}
/>

<style>
  .notes {
    display: flex;
    flex-direction: column;
    min-block-size: 100%;
    padding-inline: 10px;
    font-size: var(--text-ui);
  }

  .heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: 4px;
    padding-block: 4px;
  }

  .title {
    display: flex;
    gap: 6px;
    padding-inline: 4px;
  }

  .count {
    color: var(--color-gray-500);
  }

  .split {
    display: flex;
    overflow: hidden;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    color: var(--color-gray-900);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .create-main {
    padding: 4px 10px;
  }

  .create-main:hover,
  :global(.create-more:hover) {
    background-color: var(--color-gray-100);
  }

  :global(.create-more) {
    display: grid;
    place-items: center;
    padding: 4px 6px;
    border-inline-start: 1px solid var(--color-gray-200);
  }

  :global([data-theme='dark']) .split {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
    color: var(--color-gray-100);
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    block-size: 32px;
  }

  .search {
    display: flex;
    flex: 1;
    align-items: center;
    min-inline-size: 0;
  }

  .search > :global(svg) {
    flex-shrink: 0;
    margin-inline: 4px 12px;
  }

  .search input {
    inline-size: 100%;
    padding-block: 4px;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
  }

  .search input:focus {
    outline: none;
  }

  .search input::placeholder {
    color: var(--color-gray-400);
  }

  .clear {
    display: grid;
    padding: 2px;
    border-radius: var(--radius-pill);
  }

  .filters {
    display: flex;
    flex-shrink: 0;
    gap: 2px;
    max-inline-size: 55%;
    overflow-x: auto;
    scrollbar-width: none;
  }

  :global(.note-filter) {
    display: flex;
    align-items: center;
    gap: 4px;
    block-size: 32px;
    padding: 6px;
    border-radius: 12px;
    color: var(--color-gray-700);
    font-size: 13px;
  }

  :global(.note-filter:hover) {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark'] .note-filter) {
    color: var(--color-gray-200);
  }

  :global(.note-menu) {
    z-index: 9999;
    min-inline-size: 180px;
  }

  :global(.note-more) {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 20px;
    block-size: 20px;
    border-radius: 8px;
    color: var(--color-gray-400);
  }

  :global(.note-more:hover) {
    color: var(--color-gray-700);
  }

  .grow {
    flex: 1;
    min-inline-size: 0;
  }

  .hidden {
    visibility: hidden;
  }

  .undo {
    display: flex;
    gap: 8px;
    margin: 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .undo button {
    color: inherit;
    text-decoration: underline;
  }

  .empty {
    margin: auto;
    padding-block-end: 64px;
    text-align: center;
  }

  .empty-title {
    margin-block-end: 6px;
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .empty-title {
    color: var(--color-gray-100);
  }

  .empty-hint {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .columns {
    display: flex;
    gap: 8px;
    margin-block-start: 4px;
    padding: 0 8px 8px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
  }

  .owner-space {
    display: none;
    inline-size: 196px;
  }

  @media (min-width: 48rem) {
    .owner-space {
      display: block;
    }
  }

  .date-col {
    inline-size: 96px;
    text-align: end;
  }

  .group {
    padding: 0 8px 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .rows {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-block-end: 12px;
  }

  .row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-block-size: 32px;
    padding: 6px 8px;
    border-radius: 12px;
    transition: background-color 150ms;
  }

  .row:hover {
    background-color: var(--color-gray-50);
  }

  :global([data-theme='dark']) .row:hover {
    background-color: var(--color-gray-900);
  }

  .main {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 8px;
    min-inline-size: 0;
  }

  .name {
    overflow: hidden;
    color: var(--color-gray-800);
    font-size: 13px;
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .row:hover .name,
  .card:hover .name {
    text-decoration: underline;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-gray-200);
  }

  .age {
    flex-shrink: 0;
    color: var(--color-gray-400);
    font-size: 11px;
    line-height: 20px;
  }

  .owner {
    display: none;
    max-inline-size: 176px;
    overflow: hidden;
    color: var(--color-gray-500);
    font-size: 11px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  @media (min-width: 48rem) {
    .owner {
      display: block;
    }
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 8px;
    margin-block-end: 12px;
  }

  .card {
    display: flex;
    flex-direction: column;
    min-block-size: 128px;
    padding: 10px;
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    transition: background-color 150ms;
  }

  .card:hover {
    background-color: color-mix(in srgb, var(--color-gray-100) 60%, transparent);
  }

  :global([data-theme='dark']) .card {
    background-color: color-mix(in srgb, var(--color-gray-900) 30%, transparent);
  }

  .card-top {
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }

  .preview {
    display: -webkit-box;
    margin-block-start: 4px;
    overflow: hidden;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 20px;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
    line-clamp: 3;
  }

  .card-foot {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    margin-block-start: auto;
    padding-block-start: 12px;
    color: var(--color-gray-500);
    font-size: 11px;
    line-height: 16px;
  }

  :is(.create-main, .clear, .main, .undo button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
