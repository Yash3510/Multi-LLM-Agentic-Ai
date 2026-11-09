<script lang="ts">
  // A prompt (workspace look §6.3, features F95 to F98): name and command (saved half a second
  // after typing stops), tags and id, the version history, and the chosen version's text with
  // Set as Production and delete. Edit adds a new version.
  import { untrack } from 'svelte';
  import { resolve } from '$app/paths';
  import type { DataSource, Prompt, PromptVersion } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { COMMAND_RULE, isCommand, versionDate } from '$lib/ui/prompts';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import EditPromptDialog from './EditPromptDialog.svelte';
  import Menu from './Menu.svelte';
  import TagInput from './TagInput.svelte';

  type Props = { prompt: Prompt; source: DataSource };

  let { prompt, source }: Props = $props();

  // Edited here and saved back; the page remounts this for another prompt.
  let name = $state(untrack(() => prompt.name));
  let command = $state(untrack(() => prompt.command));
  let tags = $state(untrack(() => [...prompt.tags]));
  let saved = untrack(() => ({
    name: prompt.name,
    command: prompt.command,
    tags: [...prompt.tags],
  }));
  let live = $state(untrack(() => prompt.liveVersion));
  let liveContent = $state(untrack(() => prompt.content));
  let problem = $state('');
  let notice = $state('');
  let timer: ReturnType<typeof setTimeout> | undefined;

  let versions = $state<PromptVersion[]>([]);
  let loaded = $state(false);
  let chosen = $state<string>();
  let editing = $state(false);
  let deleting = $state<string>();
  let copied = $state(false);

  const shown = $derived(versions.find((one) => one.id === chosen));
  const text = $derived(shown?.content ?? liveContent);

  async function loadVersions(select?: string) {
    versions = await source.listVersions(prompt.id);
    loaded = true;
    chosen = select ?? versions.find((one) => one.id === live)?.id ?? versions[0]?.id;
  }

  $effect(() => {
    void untrack(() => loadVersions());
  });

  // Name, command and tags save half a second after the last change; a command that breaks the
  // rule goes back to the last saved one (F95).
  function changed() {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      if (!isCommand(command)) {
        problem = COMMAND_RULE;
        command = saved.command;
        return;
      }
      problem = '';
      await source.updatePrompt(prompt.id, { name, command, tags });
      saved = { name, command, tags: [...tags] };
      notice = 'Saved';
    }, 500);
  }

  async function copyId() {
    await navigator.clipboard?.writeText(prompt.id);
    notice = 'ID copied to clipboard';
  }

  async function copyText() {
    await navigator.clipboard?.writeText(text);
    copied = true;
    setTimeout(() => (copied = false), 2000);
  }

  async function makeLive() {
    if (!chosen) return;
    await source.setLiveVersion(prompt.id, chosen);
    live = chosen;
    liveContent = shown?.content ?? liveContent;
    notice = 'Production version updated';
  }
</script>

<div class="frame">
  <a class="back" href={resolve('/workspace/prompts')}>
    <Icon name="caret-left" size={12} /><span>Back</span>
  </a>

  <div class="head">
    <div class="identity">
      <input
        class="name"
        bind:value={name}
        oninput={changed}
        placeholder="Prompt Name"
        aria-label="Prompt Name"
        disabled={!prompt.writable}
      />
      <div class="command-row">
        <span aria-hidden="true">/</span>
        <input
          class="command"
          bind:value={command}
          oninput={changed}
          placeholder="command"
          aria-label="Command"
          disabled={!prompt.writable}
        />
      </div>
    </div>
    <div class="actions">
      {#if prompt.writable}
        <button type="button" class="chip" onclick={() => (editing = true)}>Edit</button>
        <button type="button" class="chip">
          <Icon name="lock" size={12} /><span>Access</span>
        </button>
      {:else}
        <span class="read-only">Read Only</span>
      {/if}
    </div>
  </div>

  <div class="tags-row">
    <div class="tags" onfocusout={changed}>
      <TagInput bind:tags disabled={!prompt.writable} />
    </div>
    <button type="button" class="id" title="Click to copy ID" onclick={copyId}>{prompt.id}</button>
  </div>
  {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
  <p class="sr-only" role="status">{notice}</p>

  <div class="body">
    <div class="history">
      <div class="caption history-caption">History</div>
      {#each versions as version (version.id)}
        <button
          type="button"
          class="version"
          aria-current={version.id === chosen ? 'true' : undefined}
          onclick={() => (chosen = version.id)}
        >
          <span class="bar" aria-hidden="true"></span>
          <span class="line">
            <span class="message">{version.message || 'Update'}</span>
            {#if version.id === live}<span class="live">Live</span>{/if}
          </span>
          <span class="meta">
            <span class="avatar" aria-hidden="true"><Icon name="user" size={8} /></span>
            <span class="author">{version.author.name}</span>
            <span aria-hidden="true">•</span>
            <span>{versionDate(version.created)}</span>
          </span>
        </button>
      {:else}
        {#if loaded}<p class="no-history">No history available</p>{/if}
      {/each}
    </div>

    <div class="viewer">
      <div class="viewer-head">
        <div class="viewer-title">
          <span class="caption">Prompt Content</span>
          {#if chosen}<span class="version-id">{chosen.slice(0, 7)}</span>{/if}
        </div>
        {#if prompt.writable}
          <div class="viewer-actions">
            {#if chosen === live}
              <span class="live">Live</span>
            {:else}
              <button type="button" class="set-live" onclick={makeLive}>Set as Production</button>
            {/if}
            <Menu
              label="More Options"
              backLabel="Back"
              align="end"
              items={[
                chosen === live
                  ? {
                      id: 'delete',
                      label: 'Delete',
                      icon: 'trash',
                      disabled: true,
                      reason: 'Cannot delete the production version',
                    }
                  : {
                      id: 'delete',
                      label: 'Delete',
                      icon: 'trash',
                      onSelect: () => (deleting = chosen),
                    },
              ]}
            >
              {#snippet trigger({ props })}
                <button {...props} class="version-menu" aria-label="More Options" title="More"
                  ><Icon name="dots-three" size={20} /></button
                >
              {/snippet}
            </Menu>
          </div>
        {/if}
      </div>
      <div class="text-box">
        <button type="button" class="copy" aria-label="Copy" onclick={copyText}>
          <span class:done={copied}><Icon name={copied ? 'check' : 'clipboard'} size={16} /></span>
        </button>
        <pre class="text">{text}</pre>
      </div>
    </div>
  </div>
</div>

<EditPromptDialog
  open={editing}
  content={liveContent}
  onclose={() => (editing = false)}
  onsave={async (version) => {
    await source.addVersion(prompt.id, version);
    editing = false;
    const fresh = await source.getPrompt(prompt.id);
    if (fresh) {
      live = fresh.liveVersion;
      liveContent = fresh.content;
    }
    await loadVersions();
    chosen = versions[0]?.id;
  }}
/>

<ConfirmDialog
  open={deleting !== undefined}
  title="Delete Version"
  message="Child versions will be linked to this version's parent."
  oncancel={() => (deleting = undefined)}
  onconfirm={async () => {
    const target = deleting;
    deleting = undefined;
    if (!target) return;
    await source.deleteVersion(prompt.id, target);
    await loadVersions(chosen === target ? undefined : chosen);
  }}
/>

<style>
  .frame {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
    max-block-size: 100dvh;
    padding: 0 12px 4px;
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

  .head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding-block-end: 4px;
  }

  /* The running app sets the name 3 px down and the command 3 px under it. */
  .identity {
    flex: 1;
    padding-block-start: 3px;
  }

  .name {
    inline-size: 100%;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .command-row {
    display: flex;
    gap: 2px;
    margin-block-start: 3px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .command {
    flex: 1;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .actions {
    display: flex;
    gap: 6px;
    padding-inline-end: 2px;
  }

  .chip {
    display: flex;
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

  .chip:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .chip {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
    color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .chip:hover {
    background-color: var(--color-gray-800);
  }

  .read-only {
    padding: 4px 8px;
    border-radius: 8px;
    background-color: var(--color-gray-100);
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  /* The running app sets the tag field 4 px below the id button's top, not centred. */
  .tags-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
    margin-block: 2px 6px;
  }

  .tags {
    flex: 1;
    padding-block-start: 4px;
  }

  .id {
    max-inline-size: 224px;
    padding: 2px 4px;
    overflow: hidden;
    border-radius: 6px;
    color: var(--color-gray-400);
    font-family: var(--font-mono);
    font-size: var(--text-caption);
    line-height: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: color 150ms;
  }

  .id:hover {
    color: var(--color-gray-700);
  }

  .problem {
    color: var(--color-red-600);
    font-size: var(--text-caption);
  }

  .body {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 12px;
    min-block-size: 0;
    padding-block-end: 16px;
    overflow: hidden;
  }

  @media (min-width: 48rem) {
    .body {
      flex-direction: row;
    }
  }

  .caption {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .history {
    display: none;
    flex-direction: column;
    flex-shrink: 0;
    inline-size: 256px;
    overflow-y: auto;
  }

  @media (min-width: 48rem) {
    .history {
      display: flex;
    }
  }

  .history-caption {
    margin-block-end: 8px;
  }

  .version {
    position: relative;
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    padding: 6px 6px 6px 12px;
    color: var(--color-gray-500);
    text-align: start;
    transition: color 150ms;
  }

  .version:hover {
    color: var(--color-gray-900);
  }

  .version[aria-current] {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .version:hover {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .version[aria-current] {
    color: var(--color-white);
  }

  .bar {
    position: absolute;
    inset-block: 6px;
    inset-inline-start: 0;
    inline-size: 1px;
    border-radius: var(--radius-pill);
  }

  .version[aria-current] .bar {
    background-color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .version[aria-current] .bar {
    background-color: var(--color-gray-200);
  }

  .line {
    display: flex;
    gap: 8px;
    margin-block-end: 4px;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .message {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .live {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  :global([data-theme='dark']) .live {
    color: var(--color-gray-500);
  }

  .meta {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  :global([data-theme='dark']) .meta {
    color: var(--color-gray-500);
  }

  .avatar {
    display: grid;
    place-items: center;
    inline-size: 12px;
    block-size: 12px;
    margin-inline-end: 2px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-200);
    color: var(--color-gray-500);
  }

  .author {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .no-history {
    padding-block: 24px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    font-style: italic;
    text-align: center;
  }

  .viewer {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
    overflow: hidden;
  }

  .viewer-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: 4px;
  }

  /* The monospace id would grow a shared line box; as flex items each keeps its own. */
  .viewer-title {
    display: flex;
    align-items: center;
  }

  .version-id {
    padding-inline: 4px;
    margin-inline-start: 4px;
    color: var(--color-gray-500);
    font-family: var(--font-mono);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .viewer-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .set-live {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: color 150ms;
  }

  .set-live:hover {
    color: var(--color-gray-900);
    text-decoration: underline;
  }

  .version-menu {
    display: grid;
    place-items: center;
    inline-size: 28px;
    block-size: 28px;
    border-radius: 8px;
    color: var(--color-gray-500);
    transition: background-color 150ms;
  }

  .version-menu:hover {
    background-color: var(--color-gray-50);
  }

  :global([data-theme='dark']) .version-menu:hover {
    background-color: var(--color-gray-850);
  }

  .text-box {
    position: relative;
    display: flex;
    flex: 1;
    min-block-size: 0;
  }

  .copy {
    position: absolute;
    inset-block-start: 8px;
    inset-inline-end: 8px;
    z-index: 1;
    display: grid;
    padding: 6px;
    border-radius: 8px;
    color: var(--color-gray-500);
    transition: background-color 150ms;
  }

  .copy:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .copy:hover {
    background-color: var(--color-gray-800);
  }

  .done {
    display: grid;
    color: var(--color-green-500);
  }

  .text {
    flex: 1;
    margin: 0;
    padding: 8px 32px 8px 12px;
    overflow: auto;
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 60%, transparent);
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    line-height: 1.625;
    white-space: pre-wrap;
  }

  :global([data-theme='dark']) .text {
    background-color: rgb(255 255 255 / 0.03);
  }

  :is(.back, .chip, .id, .version, .set-live, .version-menu, .copy):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
