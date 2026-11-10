<script lang="ts">
  // Models (admin look §23, F209 to F240): every base model with its visibility tag and enabled
  // switch, search, and the Actions menu (Export, Enable All, Disable All, Show All, Hide All,
  // Reset). Reset needs RESET typed and can be undone; changes save with Save and are logged.
  // Import and Manage (pulling models onto a server) wait for the 4CE server.
  import { DropdownMenu } from 'bits-ui';
  import type { DataSource } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import Logomark from './Logomark.svelte';
  import Switch from './Switch.svelte';
  import './menu.css';
  import './settings-page.css';
  import './surfaces.css';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  type Prefs = { disabled: string[]; hidden: string[] };
  let models = $state<{ id: string; name: string }[]>([]);
  let prefs = $state<Prefs>({ disabled: [], hidden: [] });
  let saved = $state<Prefs>({ disabled: [], hidden: [] });
  let query = $state('');
  let view = $state<'all' | 'enabled' | 'disabled' | 'visible' | 'hidden'>('all');
  const VIEWS = [
    ['all', 'All'],
    ['enabled', 'Enabled'],
    ['disabled', 'Disabled'],
    ['visible', 'Visible'],
    ['hidden', 'Hidden'],
  ] as const;
  let notice = $state('');
  let resetting = $state(false);
  let typed = $state('');
  let undo = $state<Prefs>();

  async function load() {
    models = [...(await source.listBaseModels())].sort((a, b) => a.name.localeCompare(b.name));
    const stored = (await source.getAdminSettings('models')) as Partial<Prefs>;
    prefs = { disabled: stored.disabled ?? [], hidden: stored.hidden ?? [] };
    saved = $state.snapshot(prefs);
  }
  void load();

  const shown = $derived(
    models
      .filter((one) => `${one.name} ${one.id}`.toLowerCase().includes(query.trim().toLowerCase()))
      .filter((one) => {
        const off = prefs.disabled.includes(one.id);
        const hid = prefs.hidden.includes(one.id);
        return (
          view === 'all' ||
          (view === 'enabled' && !off) ||
          (view === 'disabled' && off) ||
          (view === 'visible' && !hid) ||
          (view === 'hidden' && hid)
        );
      }),
  );
  const dirty = $derived(JSON.stringify(prefs) !== JSON.stringify(saved));
  const notYet = () =>
    (notice =
      'Importing and pulling models is done by the 4CE server, which is not connected in this build.');

  function setAll(key: keyof Prefs, on: boolean) {
    prefs = { ...prefs, [key]: on ? models.map((one) => one.id) : [] };
  }

  function toggle(id: string, enabled: boolean) {
    prefs = {
      ...prefs,
      disabled: enabled ? prefs.disabled.filter((one) => one !== id) : [...prefs.disabled, id],
    };
  }

  async function save() {
    await source.saveAdminSettings('models', $state.snapshot(prefs));
    saved = $state.snapshot(prefs);
    notice = 'Settings saved successfully!';
  }

  async function reset() {
    resetting = false;
    typed = '';
    undo = $state.snapshot(saved);
    prefs = { disabled: [], hidden: [] };
    await save();
    notice = 'Model settings were reset.';
  }

  async function restore() {
    if (!undo) return;
    prefs = undo;
    undo = undefined;
    await save();
  }

  function exportModels() {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(
      new Blob([JSON.stringify(models)], { type: 'application/json' }),
    );
    link.download = `models-export-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
</script>

<div class="settings-page models">
  <div class="body">
    <h2>Models <span class="count">{models.length}</span></h2>
    <div class="defaults">
      <span>Model Defaults</span>
      <button type="button" class="quiet small" onclick={notYet}>Configure</button>
    </div>
    <div class="tools">
      <label class="search">
        <Icon name="magnifying-glass" size={14} />
        <input bind:value={query} placeholder="Search Models" aria-label="Search Models" />
      </label>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger class="settings-actions view">
          <span>{VIEWS.find(([value]) => value === view)?.[1]}</span><Icon
            name="caret-down-bold"
            size={12}
          />
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            class="settings-menu"
            data-menu
            data-surface="float"
            align="end"
            sideOffset={4}
          >
            {#each VIEWS as [value, label] (value)}
              <DropdownMenu.Item data-menu-row onSelect={() => (view = value)}
                >{label}</DropdownMenu.Item
              >
            {/each}
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger class="settings-actions">
          <span>Actions</span><Icon name="caret-down-bold" size={12} />
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            class="settings-menu"
            data-menu
            data-surface="float"
            align="end"
            sideOffset={4}
          >
            <DropdownMenu.Item data-menu-row onSelect={notYet}>Import</DropdownMenu.Item>
            <DropdownMenu.Item data-menu-row onSelect={exportModels}>Export</DropdownMenu.Item>
            <DropdownMenu.Item data-menu-row onSelect={notYet}>Manage</DropdownMenu.Item>
            <DropdownMenu.Item data-menu-row onSelect={() => (resetting = true)}
              >Reset</DropdownMenu.Item
            >
            <DropdownMenu.Separator data-menu-separator />
            <DropdownMenu.Item data-menu-row onSelect={() => setAll('disabled', false)}
              >Enable All</DropdownMenu.Item
            >
            <DropdownMenu.Item data-menu-row onSelect={() => setAll('disabled', true)}
              >Disable All</DropdownMenu.Item
            >
            <DropdownMenu.Item data-menu-row onSelect={() => setAll('hidden', false)}
              >Show All</DropdownMenu.Item
            >
            <DropdownMenu.Item data-menu-row onSelect={() => setAll('hidden', true)}
              >Hide All</DropdownMenu.Item
            >
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </div>
    {#if notice}
      <p class="notice" role="status">
        {notice}
        {#if undo}<button type="button" onclick={restore}>Undo</button>{/if}
      </p>
    {/if}
    {#if shown.length}
      <ul class="list">
        {#each shown as model (model.id)}
          <li class:hidden={prefs.hidden.includes(model.id)}>
            <span class="handle" aria-hidden="true"><Icon name="dots-three" size={14} /></span>
            <Logomark size={28} />
            <span class="name">{model.name}</span>
            <span class="tag">{prefs.hidden.includes(model.id) ? 'Hidden' : 'Private'}</span>
            <span class="actions">
              <button type="button" class="icon" aria-label="Edit" title="Edit" onclick={notYet}
                ><Icon name="rename" size={14} /></button
              >
              <DropdownMenu.Root>
                <DropdownMenu.Trigger class="model-more" aria-label="More" title="More">
                  <Icon name="dots-three" size={16} />
                </DropdownMenu.Trigger>
                <DropdownMenu.Portal>
                  <DropdownMenu.Content
                    class="settings-menu"
                    data-menu
                    data-surface="float"
                    align="end"
                    sideOffset={4}
                  >
                    <DropdownMenu.Item
                      data-menu-row
                      onSelect={() =>
                        (prefs = {
                          ...prefs,
                          hidden: prefs.hidden.includes(model.id)
                            ? prefs.hidden.filter((one) => one !== model.id)
                            : [...prefs.hidden, model.id],
                        })}
                    >
                      {prefs.hidden.includes(model.id) ? 'Show' : 'Hide'}
                    </DropdownMenu.Item>
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu.Root>
              <Switch
                on={!prefs.disabled.includes(model.id)}
                label={model.name}
                onchange={(next) => toggle(model.id, next)}
              />
            </span>
          </li>
        {/each}
      </ul>
    {:else}
      <div class="empty">
        <p class="empty-title">No models found</p>
        <p class="empty-hint">
          Try adjusting your search or filter to find what you are looking for.
        </p>
      </div>
    {/if}
  </div>
  <div class="footer">
    <button type="button" class="save" disabled={!dirty} onclick={save}>Save</button>
  </div>
</div>

<ConfirmDialog
  open={resetting}
  title="Reset All Models"
  message="This resets every model's enabled and visibility settings. Type RESET to confirm; you can undo it straight after."
  confirmLabel="Reset"
  confirmDisabled={typed.trim() !== 'RESET'}
  onconfirm={reset}
  oncancel={() => {
    resetting = false;
    typed = '';
  }}
>
  <input class="typed" bind:value={typed} placeholder="RESET" aria-label="Confirmation" />
</ConfirmDialog>

<style>
  /* Measured against the running app: title 10 px above Model Defaults, a 32 px toolbar with
     14 px search text and 13 px menus, and 28 px rows 9 px apart. */
  .models h2 {
    margin-block-end: 10px;
  }

  .models .tools {
    block-size: 32px;
    margin-block: 8px 10px;
  }

  .models .tools .search {
    gap: 12px;
    padding-inline-start: 4px;
  }

  .models .tools .search input {
    block-size: 28px;
    font-size: var(--text-ui);
  }

  .models :global(.settings-actions) {
    block-size: 32px;
    font-size: 13px;
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 9px;
  }

  :global(.model-more),
  .icon {
    display: grid;
    place-items: center;
    inline-size: 26px;
    block-size: 26px;
    border-radius: 8px;
    color: var(--color-gray-500);
  }

  .count {
    margin-inline-start: 8px;
    color: var(--color-gray-500);
    font-weight: 400;
  }

  .defaults {
    line-height: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  .small {
    font-size: 11px;
  }

  .tools {
    margin-block: 8px 4px;
  }

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

  .list li {
    display: flex;
    align-items: center;
    gap: 10px;
    min-block-size: 28px;
  }

  .list li.hidden .name {
    opacity: 0.5;
  }

  .handle {
    display: grid;
    place-items: center;
    inline-size: 14px;
    color: var(--color-gray-400);
    transform: rotate(90deg);
  }

  .list :global(img) {
    border-radius: var(--radius-pill);
  }

  .name {
    line-height: 16px;
    overflow: hidden;
    color: var(--color-gray-900);
    font-size: 13px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-white);
  }

  .tag {
    line-height: 16px;
    color: var(--color-gray-500);
    font-size: 11px;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-inline-start: auto;
  }

  .save:disabled {
    cursor: default;
    opacity: 0.4;
  }

  .empty {
    max-inline-size: 384px;
    margin-inline: auto;
    padding: 64px 0 96px;
    text-align: center;
  }

  .empty-hint {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .typed {
    inline-size: 100%;
    margin-block-start: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    font-size: var(--text-ui);
  }
</style>
