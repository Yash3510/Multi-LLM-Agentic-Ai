<script lang="ts">
  // The note editor (notes look §2, F21 to F70): title with Generate, the created time and word
  // and character counts, the text, and Enhance, which streams a clearer rewrite from the model.
  // Changes save half a second after typing stops. The text is plain Markdown (no rich-text
  // editor package); recording and chatting with a note are not built yet.
  import { untrack } from 'svelte';
  import type { DataSource, Note } from '$lib/data';
  import { calendarDay } from '$lib/ui/ago';
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = { source: DataSource; note: Note; ondeleted: () => void };

  let { source, note, ondeleted }: Props = $props();

  const start = untrack(() => note);
  let title = $state(start.title);
  let content = $state(start.content);
  let enhancing = $state<AbortController>();
  let timer: ReturnType<typeof setTimeout> | undefined;

  const words = $derived(content.trim() ? content.trim().split(/\s+/).length : 0);
  // "Today at 3:04 PM", "Yesterday at …", "Last Monday at …", else the date (notes look §2).
  const created = $derived.by(() => {
    const day = calendarDay(start.created);
    const time = start.created.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    return /\d/.test(day) ? start.created.toLocaleDateString('en-GB') : `${day} at ${time}`;
  });

  function queueSave() {
    clearTimeout(timer);
    timer = setTimeout(() => void source.updateNote(start.id, { title, content }), 500);
  }

  function generateTitle() {
    title = content.trim().split(/\s+/).slice(0, 6).join(' ') || 'Untitled';
    queueSave();
  }

  async function enhance() {
    if (enhancing) {
      enhancing.abort();
      return;
    }
    const controller = new AbortController();
    enhancing = controller;
    const original = content;
    content = '';
    try {
      for await (const piece of source.enhanceNote(original, controller.signal)) content += piece;
    } finally {
      enhancing = undefined;
      queueSave();
    }
  }

  async function remove() {
    await source.deleteNote(start.id);
    ondeleted();
  }
</script>

<div class="editor">
  <div class="top">
    <input
      class="title"
      bind:value={title}
      oninput={queueSave}
      placeholder="Title"
      aria-label="Title"
      disabled={start.readOnly}
    />
    <button
      type="button"
      class="icon"
      aria-label="Generate"
      title="Generate"
      onclick={generateTitle}><Icon name="lightning" size={14} /></button
    >
    {#if start.readOnly}
      <span class="readonly">Read-Only Access</span>
    {:else}
      <button type="button" class="icon" aria-label="Delete note" title="Delete" onclick={remove}
        ><Icon name="trash" size={16} /></button
      >
    {/if}
  </div>
  <div class="meta">
    <span>{created}</span>
    <span>{words} words</span>
    <span>{content.length} characters</span>
  </div>
  <textarea
    class="body"
    bind:value={content}
    oninput={queueSave}
    placeholder="Write something..."
    aria-label="Note"
    disabled={start.readOnly || enhancing !== undefined}></textarea>
  {#if !start.readOnly}
    <button
      type="button"
      class="ai"
      aria-label={enhancing ? 'Stop' : 'Enhance'}
      title={enhancing ? 'Stop' : 'Enhance'}
      onclick={enhance}><Icon name={enhancing ? 'stop' : 'lightning'} size={18} /></button
    >
  {/if}
</div>

<style>
  .editor {
    position: relative;
    display: flex;
    flex-direction: column;
    block-size: 100%;
    padding-block-start: 8px;
  }

  .top {
    display: flex;
    align-items: center;
    gap: 2px;
    padding-inline: 12px;
  }

  .title {
    flex: 1;
    min-inline-size: 0;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
  }

  .title:focus,
  .body:focus {
    outline: none;
  }

  .title::placeholder,
  .body::placeholder {
    color: var(--color-gray-400);
  }

  .icon {
    display: grid;
    place-items: center;
    padding: 4px;
    border-radius: 8px;
    color: var(--color-gray-500);
    transition: background-color 150ms;
  }

  .icon:hover {
    background-color: rgb(0 0 0 / 0.05);
    color: var(--color-black);
  }

  :global([data-theme='dark']) .icon:hover {
    background-color: rgb(255 255 255 / 0.05);
    color: var(--color-white);
  }

  .readonly {
    padding: 4px 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .meta {
    display: flex;
    gap: 2px;
    padding-inline: 6px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .meta span {
    padding: 4px 6px;
  }

  .body {
    flex: 1;
    padding: 4px 12px 64px;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    line-height: 1.6;
    resize: none;
  }

  .ai {
    position: absolute;
    inset-block-end: 14px;
    inset-inline-end: 14px;
    display: grid;
    place-items: center;
    inline-size: 36px;
    block-size: 36px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
  }

  :global([data-theme='dark']) .ai {
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :is(.icon, .ai):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
