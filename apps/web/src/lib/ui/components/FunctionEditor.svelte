<script lang="ts">
  // Create or view a function (admin look §16, F156 to F168): name, id, description, the
  // starter type on create, and the code. Saving waits for the 4CE server, so it says so and
  // changes nothing.
  import { untrack } from 'svelte';
  import { resolve } from '$app/paths';
  import type { ServerFunction } from '$lib/data';
  import { NOT_YET, STARTERS } from '$lib/ui/functions';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import CodeEditor from './CodeEditor.svelte';

  type Props = { fn?: ServerFunction };

  let { fn }: Props = $props();

  // The page re-creates the editor per function, so the first values are the ones to copy.
  const start = untrack(() => fn);
  let name = $state(start?.name ?? '');
  let id = $state(start?.id ?? '');
  let description = $state(start?.description ?? '');
  let starter = $state<keyof typeof STARTERS>('filter');
  let code = $state<string>(start?.content ?? STARTERS.filter);
  let notice = $state('');

  function pickStarter(next: keyof typeof STARTERS) {
    starter = next;
    code = STARTERS[next];
  }
</script>

<div class="editor-page">
  <a class="back" href={resolve('/admin/functions')}><Icon name="caret-left" size={12} />Back</a>
  <div class="header">
    <div class="fields">
      <input
        class="name"
        bind:value={name}
        placeholder="Function Name"
        aria-label="Function Name"
        title="e.g. My Filter"
      />
      <div class="sub">
        {#if fn}
          <span class="id fixed">{fn.id}</span>
        {:else}
          <input
            class="id"
            bind:value={id}
            placeholder="Function ID"
            aria-label="Function ID"
            title="e.g. my_filter"
          />
        {/if}
        <input
          class="description"
          bind:value={description}
          placeholder="Function Description"
          aria-label="Function Description"
          title="e.g. A filter to remove profanity from text"
        />
      </div>
    </div>
    {#if !fn}
      <select
        class="starter"
        value={starter}
        aria-label="Function starter"
        onchange={(event) => pickStarter(event.currentTarget.value as keyof typeof STARTERS)}
      >
        <option value="filter">Filter</option>
        <option value="event">Event</option>
      </select>
    {/if}
  </div>
  <div class="code"><CodeEditor value={code} onchange={(next) => (code = next)} /></div>
  <div class="footer">
    <p class="warning">
      <span class="lead">Warning:</span> Functions can execute arbitrary code.
      <span class="soft">Only install functions from sources you trust.</span>
      {#if notice}<span class="notice" role="status">{notice}</span>{/if}
    </p>
    <button type="button" class="save" onclick={() => (notice = NOT_YET)}
      >{fn ? 'Save' : 'Save & Create'}</button
    >
  </div>
</div>

<style>
  .editor-page {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    min-inline-size: 0;
    padding-inline: 16px;
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

  .header {
    display: flex;
    flex-shrink: 0;
    align-items: flex-start;
    gap: 8px;
    padding: 0 4px 8px;
  }

  .fields {
    flex: 1;
    min-inline-size: 0;
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

  .name {
    inline-size: 100%;
    font-size: var(--text-ui);
  }

  .sub {
    display: flex;
    gap: 8px;
    min-inline-size: 0;
    margin-block-start: 2px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .id {
    flex: 1;
    min-inline-size: 128px;
    font-family: var(--font-mono);
    font-size: var(--text-caption);
  }

  .id.fixed {
    flex: none;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .description {
    flex: 1;
    font-size: var(--text-caption);
  }

  .starter {
    block-size: 28px;
    padding-inline: 8px;
    border: 1px solid var(--color-gray-100);
    border-radius: 8px;
    background: transparent;
    color: inherit;
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .starter {
    border-color: var(--color-gray-800);
  }

  .code {
    flex: 1;
    min-block-size: 0;
    overflow: hidden;
    border-radius: 8px;
  }

  .footer {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding-block: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .warning {
    min-inline-size: 0;
  }

  :global([data-theme='dark']) .lead {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .soft {
    color: var(--color-gray-400);
  }

  .notice {
    display: block;
  }

  .save {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    block-size: 28px;
    padding-inline: 10px;
    border-radius: 8px;
    background-color: var(--color-gray-900);
    color: var(--color-white);
    font-size: var(--text-caption);
    transition: background-color 150ms;
  }

  .save:hover {
    background-color: var(--color-black);
  }

  :global([data-theme='dark']) .save {
    background-color: var(--color-gray-100);
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .save:hover {
    background-color: var(--color-white);
  }

  :is(.back, .save, .starter):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
