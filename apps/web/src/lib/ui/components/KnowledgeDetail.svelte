<script lang="ts">
  // A knowledge base (workspace look §5, features F66 to F77): its name and description (saved a
  // second after typing stops), then a card with search, view and sort, the path into folders,
  // the folders and documents, and a sheet to read and edit a document's text.
  import Wire from './Wire.svelte';
  import { Dialog, Popover } from 'bits-ui';
  import { untrack } from 'svelte';
  import { resolve } from '$app/paths';
  import type {
    ContentQuery,
    DataSource,
    KnowledgeBase,
    KnowledgeDocument,
    KnowledgeFolder,
  } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import ContentRow from './ContentRow.svelte';
  import Menu from './Menu.svelte';
  import NewDirectoryDialog from './NewDirectoryDialog.svelte';
  import TextComposer from './TextComposer.svelte';

  type Props = {
    base: KnowledgeBase;
    source: DataSource;
  };

  let { base, source }: Props = $props();

  // Edited here and saved back; the page remounts this for another base.
  let name = $state(untrack(() => base.name));
  let description = $state(untrack(() => base.description ?? ''));
  let problem = $state('');
  let notice = $state('');
  let timer: ReturnType<typeof setTimeout> | undefined;

  let query = $state('');
  let content = $state(false);
  let view = $state<'all' | 'mine' | 'shared'>('all');
  let sort = $state<ContentQuery['sort']>();
  let direction = $state<'asc' | 'desc'>('desc');
  let path = $state<KnowledgeFolder[]>([]);
  const folder = $derived(path.at(-1)?.id);

  let folders = $state<KnowledgeFolder[]>([]);
  let documents = $state<KnowledgeDocument[]>([]);
  let total = $state(0);
  let loading = $state(true);

  let open = $state<KnowledgeDocument>();
  let text = $state('');
  let saving = $state(false);

  let making = $state(false);
  let writing = $state(false);
  let resetting = $state(false);
  let removing = $state<KnowledgeFolder>();
  // Kept between uses (F76).
  let removeContents = $state(true);
  let dragging = $state(false);
  let filesInput = $state<HTMLInputElement>();
  let folderInput = $state<HTMLInputElement>();

  const VIEWS = { all: 'All', mine: 'Created by you', shared: 'Shared with you' } as const;
  const SORTS = { name: 'Name', created: 'Created', updated: 'Updated' } as const;

  async function load() {
    const found = await source.listContents(base.id, { folder, query, content, sort, direction });
    folders = found.folders;
    documents = found.documents;
    total = found.total;
    loading = false;
  }

  // Search waits 300 ms; every other change reloads at once (F70, F73).
  let searchTimer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    void [folder, content, sort, direction, view];
    void load();
  });

  function search(value: string) {
    query = value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(load, 300);
  }

  // Name and description save a second after the last keystroke (F68).
  function edited() {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      if (!name.trim() || !description.trim()) {
        problem = 'Please fill in all fields.';
        return;
      }
      problem = '';
      await source.updateKnowledge(base.id, { name, description });
      notice = 'Knowledge updated successfully.';
    }, 1000);
  }

  async function copyId() {
    await navigator.clipboard?.writeText(base.id);
    notice = 'ID copied to clipboard';
  }

  async function preview(doc: KnowledgeDocument) {
    open = doc;
    text = await source.getDocumentText(doc.id);
  }

  async function saveText() {
    if (!open) return;
    saving = true;
    try {
      await source.saveDocumentText(open.id, text);
      open = undefined;
      await load();
    } finally {
      saving = false;
    }
  }

  // Files go in one after another; an empty one is refused and skipped (F78). Text files keep
  // their text; for other types the server extracts it, which the API will do.
  async function upload(files: File[], into = folder) {
    for (const file of files) {
      if (file.size === 0) {
        problem = 'Cannot upload an empty file.';
        continue;
      }
      const text = file.type.startsWith('text/') || /\.(txt|md|csv)$/i.test(file.name);
      await source.addDocument(base.id, {
        name: file.name,
        text: text ? await file.text() : '',
        size: file.size,
        folder: into,
      });
    }
    await load();
  }

  // A picked folder is mirrored into the open folder: its folders made parents-first, hidden
  // files and folders skipped, nothing removed (F79).
  async function uploadFolder(files: File[]) {
    // Each folder path made so far, and its id; '' is the open folder.
    const made: Record<string, string | undefined> = { '': folder };
    for (const file of files) {
      const parts = file.webkitRelativePath.split('/');
      if (parts.some((part) => part.startsWith('.'))) continue;
      for (let depth = 1; depth < parts.length; depth++) {
        const key = parts.slice(0, depth).join('/');
        if (key in made) continue;
        const parent = made[parts.slice(0, depth - 1).join('/')];
        made[key] = (await source.createFolder(base.id, parts[depth - 1], parent)).id;
      }
      await upload([file], made[parts.slice(0, -1).join('/')]);
    }
    await load();
  }

  // Files dropped anywhere on the page are uploaded (F84).
  $effect(() => {
    if (!base.writable) return;
    const carriesFiles = (event: DragEvent) => event.dataTransfer?.types.includes('Files');
    const over = (event: DragEvent) => {
      if (!carriesFiles(event)) return;
      event.preventDefault();
      dragging = true;
    };
    const leave = (event: DragEvent) => {
      if (!event.relatedTarget) dragging = false;
    };
    const drop = (event: DragEvent) => {
      if (!carriesFiles(event)) return;
      event.preventDefault();
      dragging = false;
      void upload([...(event.dataTransfer?.files ?? [])]);
    };
    window.addEventListener('dragover', over);
    window.addEventListener('dragleave', leave);
    window.addEventListener('drop', drop);
    return () => {
      window.removeEventListener('dragover', over);
      window.removeEventListener('dragleave', leave);
      window.removeEventListener('drop', drop);
    };
  });

  function download(doc: KnowledgeDocument) {
    void source.getDocumentText(doc.id).then((body) => {
      const url = URL.createObjectURL(new Blob([body], { type: 'text/plain' }));
      window.open(url, '_blank', 'noopener');
    });
  }
</script>

<div class="frame">
  <div class="head">
    <a class="back" href={resolve('/workspace/knowledge')}>
      <Icon name="caret-left" size={12} /><span>Back</span>
    </a>
    <div class="meta">
      <div class="name-row">
        <input
          class="name"
          bind:value={name}
          oninput={edited}
          placeholder="Knowledge Name"
          aria-label="Knowledge Name"
          disabled={!base.writable}
        />
        {#if total}<span class="count">{total} files</span>{/if}
        {#if base.writable}
          <button type="button" class="access">
            <Icon name="lock" size={12} /><span>Access</span>
          </button>
        {:else}
          <span class="count">Read Only</span>
        {/if}
      </div>
      <div class="description-row">
        <input
          class="description"
          bind:value={description}
          oninput={edited}
          placeholder="Knowledge Description"
          aria-label="Knowledge Description"
          disabled={!base.writable}
        />
        <button type="button" class="id" title="Click to copy ID" onclick={copyId}>{base.id}</button
        >
      </div>
      {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
      <p class="sr-only" role="status">{notice}</p>
    </div>
  </div>

  <div class="card">
    <div class="search-row">
      <span class="search-icon"><Icon name="magnifying-glass" size={14} /></span>
      <input
        class="search"
        value={query}
        oninput={(event) => search(event.currentTarget.value)}
        onfocus={() => (open = undefined)}
        placeholder="Search Collection"
        aria-label="Search Collection"
      />
      <Popover.Root>
        <Popover.Trigger class="content-options" aria-label="Search options">
          <Icon name="sliders-bold" size={14} />
        </Popover.Trigger>
        <Popover.Portal>
          <Popover.Content class="content-menu" side="bottom" align="end" sideOffset={4}>
            <label class="content-item">
              <input type="checkbox" bind:checked={content} />
              File content
            </label>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
      {#if base.writable}
        <Menu
          label="Add Content"
          backLabel="Back"
          align="end"
          items={[
            {
              id: 'directory',
              label: 'New directory',
              icon: 'folder-plus',
              onSelect: () => (making = true),
            },
            { type: 'separator' },
            {
              id: 'files',
              label: 'Upload files',
              icon: 'upload-bold',
              onSelect: () => filesInput?.click(),
            },
            {
              id: 'folder',
              label: 'Upload directory',
              icon: 'folder-open-bold',
              onSelect: () => folderInput?.click(),
            },
            {
              id: 'text',
              label: 'Add text content',
              icon: 'add-text-bold',
              onSelect: () => (writing = true),
            },
            { type: 'separator' },
            { id: 'reset', label: 'Reset', icon: 'reset-bold', onSelect: () => (resetting = true) },
          ]}
        >
          {#snippet trigger({ props })}
            <button {...props} class="add" aria-label="Add Content" title="Add Content"
              ><Icon name="plus" size={16} /></button
            >
          {/snippet}
        </Menu>
        <input
          bind:this={filesInput}
          type="file"
          multiple
          hidden
          onchange={(event) => {
            void upload([...(event.currentTarget.files ?? [])]);
            event.currentTarget.value = '';
          }}
        />
        <input
          bind:this={folderInput}
          type="file"
          webkitdirectory
          hidden
          onchange={(event) => {
            void uploadFolder([...(event.currentTarget.files ?? [])]);
            event.currentTarget.value = '';
          }}
        />
      {/if}
    </div>

    <div class="controls">
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
            options: Object.entries(VIEWS).map(([value, label]) => ({ value, label })),
            onChange: (value) => (view = value as typeof view),
          },
        ]}
      >
        {#snippet trigger({ props })}
          <button {...props} class="drop view"
            ><span class="truncate">{VIEWS[view]}</span><Icon
              name="caret-down-bold"
              size={12}
            /></button
          >
        {/snippet}
      </Menu>
      <Menu
        label="Sort"
        backLabel="Back"
        align="end"
        items={[
          {
            type: 'choices',
            id: 'sort',
            label: 'Sort',
            value: sort ?? '',
            options: Object.entries(SORTS).map(([value, label]) => ({ value, label })),
            onChange: (value) => (sort = value as typeof sort),
          },
        ]}
      >
        {#snippet trigger({ props })}
          <button {...props} class="drop"
            ><span class="truncate">{sort ? SORTS[sort] : 'Sort'}</span><Icon
              name="caret-down-bold"
              size={12}
            /></button
          >
        {/snippet}
      </Menu>
      {#if sort}
        <Menu
          label="Direction"
          backLabel="Back"
          align="end"
          items={[
            {
              type: 'choices',
              id: 'direction',
              label: 'Direction',
              value: direction,
              options: [
                { value: 'asc', label: 'Asc' },
                { value: 'desc', label: 'Desc' },
              ],
              onChange: (value) => (direction = value as typeof direction),
            },
          ]}
        >
          {#snippet trigger({ props })}
            <button {...props} class="drop"
              ><span class="truncate">{direction === 'asc' ? 'Asc' : 'Desc'}</span><Icon
                name="caret-down-bold"
                size={12}
              /></button
            >
          {/snippet}
        </Menu>
      {/if}
    </div>

    {#if path.length}
      <nav class="crumbs" aria-label="Breadcrumb">
        <button type="button" class="crumb" onclick={() => (path = [])}>{name}</button>
        {#each path as step, index (step.id)}
          <span class="sep" aria-hidden="true"><Icon name="caret-right" size={12} /></span>
          <button
            type="button"
            class="crumb"
            aria-current={index === path.length - 1 ? 'location' : undefined}
            onclick={() => (path = path.slice(0, index + 1))}>{step.name}</button
          >
        {/each}
      </nav>
    {/if}

    <div class="list">
      {#if loading}
        <div class="loading"><Wire width={48} label="Loading" /></div>
      {:else if folders.length || documents.length}
        {#each folders as item (item.id)}
          <ContentRow
            {item}
            kind="folder"
            writable={base.writable}
            onopen={() => {
              open = undefined;
              path = [...path, item];
            }}
            onrename={async (next) => {
              await source.renameItem(base.id, item.id, next);
              await load();
            }}
            ondelete={() => (removing = item)}
          />
        {/each}
        {#each documents as item (item.id)}
          <ContentRow
            {item}
            kind="document"
            writable={base.writable}
            onopen={() => preview(item)}
            onrename={async (next) => {
              await source.renameItem(base.id, item.id, next);
              await load();
            }}
            ondelete={async () => {
              if (open?.id === item.id) open = undefined;
              await source.removeDocument(base.id, item.id);
              await load();
            }}
            ondownload={() => download(item)}
          />
        {/each}
      {:else}
        <p class="empty">No content found</p>
      {/if}
    </div>
  </div>
</div>

<NewDirectoryDialog
  open={making}
  onclose={() => (making = false)}
  oncreate={async (folderName) => {
    await source.createFolder(base.id, folderName, folder);
    making = false;
    await load();
  }}
/>

<TextComposer
  open={writing}
  onclose={() => (writing = false)}
  onsave={async (title, body) => {
    await source.addDocument(base.id, { name: `${title}.txt`, text: body, folder });
    writing = false;
    await load();
  }}
/>

<ConfirmDialog
  open={resetting}
  title="Reset knowledge base?"
  message="This will remove all files and folders from this knowledge base. This action cannot be undone."
  oncancel={() => (resetting = false)}
  onconfirm={async () => {
    resetting = false;
    await source.resetKnowledge(base.id);
    await load();
  }}
/>

<ConfirmDialog
  open={removing !== undefined}
  title="Delete directory?"
  message="Are you sure you want to delete this directory?"
  oncancel={() => (removing = undefined)}
  onconfirm={async () => {
    const target = removing;
    removing = undefined;
    if (!target) return;
    await source.deleteFolder(base.id, target.id, { contents: removeContents });
    await load();
  }}
>
  <label class="remove-contents">
    <input type="checkbox" bind:checked={removeContents} />
    Delete all contents inside this directory
  </label>
</ConfirmDialog>

{#if dragging}
  <div class="dropzone" role="region" aria-label="Drag and Drop Container">
    <div class="dropzone-inner">
      <h2>Add Files</h2>
      <p>Drop any files here to upload</p>
    </div>
  </div>
{/if}

<Dialog.Root open={open !== undefined} onOpenChange={(next) => !next && (open = undefined)}>
  <Dialog.Portal>
    <Dialog.Overlay class="sheet-backdrop" />
    <Dialog.Content class="sheet" aria-describedby={undefined}>
      <div class="sheet-head">
        <Dialog.Close class="sheet-back" aria-label="Close"
          ><Icon name="caret-left" size={16} /></Dialog.Close
        >
        <Dialog.Title class="sheet-title">{open?.name}</Dialog.Title>
        {#if base.writable}
          <button type="button" class="sheet-save" disabled={saving} onclick={saveText}>
            Save
            {#if saving}<span class="saving"><Wire /></span>{/if}
          </button>
        {/if}
      </div>
      <textarea
        class="sheet-text"
        bind:value={text}
        placeholder="Add content here"
        aria-label="Content"
        readonly={!base.writable}></textarea>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .frame {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
    inline-size: 100%;
    padding: 0 12px 4px;
  }

  .head {
    padding-inline: 8px;
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

  .meta {
    padding-inline: 4px;
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

  .name-row,
  .description-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    inline-size: 100%;
  }

  .name {
    flex: 1;
    min-inline-size: 0;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .count {
    flex-shrink: 0;
    margin-inline-end: 10px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
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

  .description {
    flex: 1;
    min-inline-size: 0;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .id {
    display: none;
    flex-shrink: 0;
    padding: 4px 8px;
    border-radius: 8px;
    color: var(--color-gray-500);
    font-family: var(--font-mono);
    font-size: var(--text-caption);
    line-height: 16px;
    white-space: nowrap;
  }

  .id:hover {
    text-decoration: underline;
  }

  @media (min-width: 48rem) {
    .id {
      display: block;
    }
  }

  .problem {
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }

  .card {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
    margin-block: 6px 8px;
    padding-block: 6px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 30%, transparent);
    border-radius: 24px;
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .card {
    border-color: color-mix(in srgb, var(--color-gray-850) 30%, transparent);
    background-color: var(--color-gray-900);
  }

  .search-row {
    display: flex;
    align-items: center;
    padding-inline: 12px;
  }

  .search-icon {
    display: inline-flex;
    margin-inline: 4px 8px;
  }

  .search {
    flex: 1;
    min-inline-size: 0;
    padding-block: 4px;
    padding-inline-end: 16px;
    border-radius: var(--radius-pill);
    font-size: var(--text-caption);
    line-height: 16px;
    padding-inline: 12px;
    background-image: var(--field-inset-fill);
    box-shadow: var(--field-inset-edge);
  }

  :global(.content-options),
  .add {
    display: grid;
    place-items: center;
    padding: 6px;
    border-radius: 12px;
    transition: color 150ms;
  }

  :global(.content-options) {
    margin-inline-end: 4px;
    color: var(--color-gray-500);
  }

  :global(.content-options:hover),
  .add:hover {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark'] .content-options:hover),
  :global([data-theme='dark']) .add:hover {
    color: var(--color-gray-100);
  }

  :global(.content-menu) {
    z-index: 9999;
    min-inline-size: 180px;
    padding: 2px;
    border: 1px solid var(--color-gray-100);
    border-radius: 12px;
    background-color: var(--color-white);
    box-shadow:
      0 10px 15px -3px rgb(0 0 0 / 0.1),
      0 4px 6px -4px rgb(0 0 0 / 0.1);
  }

  :global([data-theme='dark'] .content-menu) {
    border-color: var(--color-gray-800);
    background-color: var(--color-gray-850);
  }

  .content-item {
    display: flex;
    align-items: center;
    gap: 8px;
    block-size: 27px;
    padding-inline: 8px;
    font-size: var(--text-small);
  }

  .controls {
    display: flex;
    gap: 8px;
    padding-inline: 12px;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .drop {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    block-size: 32px;
    padding: 6px;
    border-radius: 12px;
    color: var(--color-gray-700);
    font-size: var(--text-small);
    line-height: calc(20 / 14);
    transition: color 150ms;
  }

  .drop.view {
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .drop:hover {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .drop {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .drop:hover {
    color: var(--color-gray-100);
  }

  .crumbs {
    display: flex;
    align-items: center;
    margin-block-end: 4px;
    padding-inline: 16px;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .crumb {
    flex-shrink: 0;
    padding-block: 2px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: color 150ms;
  }

  .crumb:hover {
    color: var(--color-gray-600);
    text-decoration: underline;
  }

  .crumb[aria-current] {
    color: var(--color-gray-700);
  }

  .sep {
    display: inline-flex;
    margin-inline: 2px;
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .crumb {
    color: var(--color-gray-500);
  }

  :global([data-theme='dark']) .crumb[aria-current] {
    color: var(--color-gray-300);
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 0.5px;
    min-block-size: 0;
    padding-inline: 8px;
    overflow-y: auto;
    scrollbar-width: none;
  }

  .empty {
    margin-block: 12px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    text-align: center;
  }

  .loading {
    display: flex;
    justify-content: center;
    margin-block: 40px;
  }

  .saving {
    display: inline-flex;
    margin-inline-start: 8px;
  }

  :global(.sheet-backdrop) {
    position: fixed;
    inset: 0;
    z-index: 999;
    background-color: rgb(0 0 0 / 0.6);
  }

  :global(.sheet) {
    position: fixed;
    inset: 0;
    z-index: 999;
    display: flex;
    flex-direction: column;
    background-color: var(--color-gray-50);
    animation: rise 100ms ease-out;
  }

  :global([data-theme='dark'] .sheet) {
    background-color: var(--color-gray-900);
    color: var(--color-gray-100);
  }

  @keyframes rise {
    from {
      translate: 0 100px;
    }
  }

  .sheet-head {
    display: flex;
    align-items: center;
    padding: 8px;
  }

  :global(.sheet-back) {
    display: grid;
    margin-inline-end: 8px;
    padding: 6px;
    border-radius: 8px;
  }

  :global(.sheet-back:hover) {
    background-color: rgb(0 0 0 / 0.05);
  }

  :global(.sheet-title) {
    flex: 1;
    overflow: hidden;
    font-size: var(--text-ui);
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .sheet-save {
    display: flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .sheet-save:hover {
    background-color: rgb(0 0 0 / 0.05);
  }

  .sheet-save:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  .sheet-text {
    flex: 1;
    padding: 8px 12px;
    background: transparent;
    color: inherit;
    font-size: var(--text-caption);
    line-height: 16px;
    resize: none;
  }

  .sheet-text:focus {
    outline: none;
  }

  :is(.back, .access, .id, .add, .drop, .crumb):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }

  .remove-contents {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-block-start: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .dropzone {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    justify-content: center;
    background-color: color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    backdrop-filter: blur(4px);
    pointer-events: none;
  }

  :global([data-theme='dark']) .dropzone {
    background-color: color-mix(in srgb, var(--color-gray-900) 80%, transparent);
  }

  .dropzone-inner {
    max-inline-size: 448px;
    margin: auto;
    text-align: center;
  }

  .dropzone h2 {
    font-size: 24px;
    font-weight: 400;
    line-height: 32px;
  }

  .dropzone p {
    margin-block-start: 8px;
    padding-inline: 8px;
    color: var(--color-gray-700);
    font-size: 16px;
    line-height: 24px;
  }

  :global([data-theme='dark']) .dropzone h2 {
    color: var(--color-white);
  }

  :global([data-theme='dark']) .dropzone p {
    color: var(--color-gray-200);
  }

  @media (prefers-reduced-motion: reduce) {
    :global(.sheet) {
      animation: none;
    }
  }
</style>
