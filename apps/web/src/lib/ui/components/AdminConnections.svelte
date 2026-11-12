<script lang="ts">
  // Connections (admin look §22): model servers speaking the OpenAI-compatible API or Ollama's,
  // each a list of addresses with an enabled switch and a settings dialog; and the cached base
  // model list. Only local or self-hosted addresses are accepted, as the owner chose; Direct
  // Connections (people's own endpoints) are left out.
  import { toast } from '$lib/ui/toast.svelte';
  import type { DataSource } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConnectionDialog, { type Connection } from './ConnectionDialog.svelte';
  import Switch from './Switch.svelte';
  import './settings-page.css';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  type Kind = 'openai' | 'ollama';
  type Config = {
    ENABLE_OPENAI_API: boolean;
    ENABLE_OLLAMA_API: boolean;
    OPENAI_CONNECTIONS: Connection[];
    OLLAMA_CONNECTIONS: Connection[];
    ENABLE_BASE_MODELS_CACHE: boolean;
  };
  const DEFAULTS: Config = {
    ENABLE_OPENAI_API: true,
    ENABLE_OLLAMA_API: false,
    OPENAI_CONNECTIONS: [{ url: 'http://localhost:1234/v1', key: '', enabled: true }],
    OLLAMA_CONNECTIONS: [{ url: 'http://localhost:11434', key: '', enabled: true }],
    ENABLE_BASE_MODELS_CACHE: false,
  };

  let config = $state<Config>();
  let editing = $state<{ kind: Kind; index?: number }>();
  let notice = $state('');

  async function load() {
    config = {
      ...DEFAULTS,
      ...((await source.getAdminSettings('connections')) as Partial<Config>),
    };
  }
  void load();

  const listKey = (kind: Kind) => (kind === 'openai' ? 'OPENAI_CONNECTIONS' : 'OLLAMA_CONNECTIONS');

  function saveConnection(connection: Connection) {
    if (!config || !editing) return;
    const key = listKey(editing.kind);
    const list = [...config[key]];
    if (editing.index === undefined) list.push(connection);
    else list[editing.index] = connection;
    config = { ...config, [key]: list };
    editing = undefined;
  }

  function removeConnection() {
    if (!config || editing?.index === undefined) return;
    const key = listKey(editing.kind);
    config = { ...config, [key]: config[key].filter((_, at) => at !== editing?.index) };
    editing = undefined;
  }

  function toggle(kind: Kind, index: number, enabled: boolean) {
    if (!config) return;
    const key = listKey(kind);
    config = {
      ...config,
      [key]: config[key].map((one, at) => (at === index ? { ...one, enabled } : one)),
    };
  }

  async function save(event: SubmitEvent) {
    event.preventDefault();
    if (!config) return;
    await source.saveAdminSettings('connections', $state.snapshot(config));
    toast('Settings saved successfully!');
  }
</script>

{#snippet provider(kind: Kind, label: string, enable: 'ENABLE_OPENAI_API' | 'ENABLE_OLLAMA_API')}
  {#if config}
    <div class="block">
      <div class="row">
        <span>{label}</span>
        <Switch
          on={config[enable]}
          {label}
          onchange={(next) => config && (config = { ...config, [enable]: next })}
        />
      </div>
      {#if config[enable]}
        <div class="manage">
          <span>Manage {label} Connections</span>
          <button
            type="button"
            class="add"
            aria-label="Add Connection"
            title="Add Connection"
            onclick={() => (editing = { kind })}><Icon name="plus" size={16} /></button
          >
        </div>
        <div class="list">
          {#each config[listKey(kind)] as connection, index (index)}
            <div class="connection">
              <span class="url" title={connection.url}>{connection.url}</span>
              <button
                type="button"
                class="gear"
                aria-label="Configure"
                title="Configure"
                onclick={() => (editing = { kind, index })}
                ><Icon name="gear-six" size={16} /></button
              >
              <Switch
                on={connection.enabled}
                label={connection.url}
                onchange={(next) => toggle(kind, index, next)}
              />
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
{/snippet}

<form class="settings-page" onsubmit={save}>
  <div class="body">
    <h2>Connections</h2>
    {#if config}
      <section>
        <div class="rows grouped">
          {@render provider('openai', 'OpenAI API', 'ENABLE_OPENAI_API')}
          {@render provider('ollama', 'Ollama API', 'ENABLE_OLLAMA_API')}
        </div>
      </section>
      <section class="user">
        <h3 class="heading">User Connections</h3>
        <div class="rows grouped">
          <div class="block">
            <div class="row">
              <span>Cache Base Model List</span>
              <Switch
                on={config.ENABLE_BASE_MODELS_CACHE}
                label="Cache Base Model List"
                onchange={(next) =>
                  config && (config = { ...config, ENABLE_BASE_MODELS_CACHE: next })}
              />
            </div>
            <p class="note">
              Base Model List Cache speeds up access by fetching base models only at startup or on
              settings save—faster, but may not show recent base model changes.
            </p>
          </div>
        </div>
      </section>
    {/if}
  </div>
  <p class="sr-only" role="status">{notice}</p>
  <div class="footer"><button type="submit" class="save">Save</button></div>
</form>

<ConnectionDialog
  open={editing !== undefined}
  connection={editing?.index === undefined || !config
    ? undefined
    : config[listKey(editing.kind)][editing.index]}
  onsave={saveConnection}
  ondelete={removeConnection}
  onclose={() => (editing = undefined)}
/>

<style>
  .user {
    margin-block-start: 20px;
  }

  .heading {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .heading {
    color: var(--color-gray-600);
  }

  .manage {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .manage {
    color: var(--color-gray-400);
  }

  .add,
  .gear {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    border-radius: 8px;
    color: var(--color-gray-400);
    transition:
      background-color 150ms,
      color 150ms;
  }

  .add:hover,
  .gear:hover {
    background-color: rgb(0 0 0 / 0.05);
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) :is(.add, .gear) {
    color: var(--color-gray-600);
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .connection {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .url {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
    font-size: var(--text-ui);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :is(.add, .gear):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
