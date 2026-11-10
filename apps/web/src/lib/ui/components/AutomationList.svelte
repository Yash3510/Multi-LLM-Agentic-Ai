<script lang="ts">
  // Automations (automations look §2): search, status filter, Enable All / Disable All, and a
  // row per automation with its schedule, next run, menu (Edit, Run now, Delete with Undo) and
  // Active switch.
  import { DropdownMenu } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { Automation, DataSource } from '$lib/data';
  import { nextRun, scheduleLabel } from '$lib/ui/automations';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import Switch from './Switch.svelte';
  import './menu.css';
  import './surfaces.css';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  let automations = $state<Automation[]>();
  let query = $state('');
  let status = $state<'all' | 'active' | 'paused'>('all');
  let deleting = $state<Automation>();
  let undo = $state<Automation>();

  async function load() {
    automations = await source.listAutomations();
  }
  void load();

  const shown = $derived(
    (automations ?? [])
      .filter((one) => one.name.toLowerCase().includes(query.trim().toLowerCase()))
      .filter((one) => status === 'all' || (status === 'active') === one.active),
  );
  const when = (date?: Date) =>
    date
      ? date.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' })
      : 'Not scheduled';

  async function setActive(automation: Automation, active: boolean) {
    const one = $state.snapshot(automation) as Automation;
    await source.saveAutomation({
      id: one.id,
      name: one.name,
      prompt: one.prompt,
      model: one.model,
      schedule: one.schedule,
      destination: one.destination,
      active,
    });
    await load();
  }

  async function setAll(active: boolean) {
    for (const one of automations ?? []) await setActive(one, active);
  }

  async function remove() {
    if (!deleting) return;
    const gone = deleting;
    deleting = undefined;
    await source.deleteAutomation(gone.id);
    undo = gone;
    await load();
  }

  async function restore() {
    if (!undo) return;
    await source.restoreAutomation(undo.id);
    undo = undefined;
    await load();
  }
</script>

<div class="automations">
  <div class="heading" data-page-bar>
    <span class="title">Automations <span class="count">{shown.length}</span></span>
    <a class="create" href={resolve('/automations/create')}>Create</a>
  </div>
  <div class="toolbar">
    <label class="search">
      <Icon name="magnifying-glass" size={14} />
      <input bind:value={query} placeholder="Search Automations" aria-label="Search Automations" />
    </label>
    <select class="status" bind:value={status} aria-label="Status">
      <option value="all">All</option><option value="active">Active</option><option value="paused"
        >Paused</option
      >
    </select>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger class="settings-actions"
        >Actions<Icon name="caret-down-bold" size={12} /></DropdownMenu.Trigger
      >
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          class="auto-menu"
          data-menu
          data-surface="float"
          align="end"
          sideOffset={4}
        >
          <DropdownMenu.Item data-menu-row onSelect={() => setAll(true)}
            >Enable All</DropdownMenu.Item
          >
          <DropdownMenu.Item data-menu-row onSelect={() => setAll(false)}
            >Disable All</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  </div>
  {#if undo}<p class="undo" role="status">
      Deleted {undo.name}. <button type="button" onclick={restore}>Undo</button>
    </p>{/if}
  {#if automations && !shown.length}
    <div class="empty">
      <p class="empty-title">{automations.length ? 'No results found' : 'No automations'}</p>
      {#if !automations.length}<p class="empty-hint">
          Run a prompt on a schedule. Create one to get started.
        </p>{/if}
    </div>
  {:else}
    <ul class="rows">
      {#each shown as automation (automation.id)}
        <li class="row">
          <a class="main" href={resolve('/automations/[id]', { id: automation.id })}>
            <span class="name">{automation.name}</span>
            <span class="schedule">{scheduleLabel(automation.schedule)}</span>
            <span class="next"
              >Next run: {automation.active ? when(nextRun(automation.schedule)) : 'Paused'}</span
            >
          </a>
          <DropdownMenu.Root>
            <DropdownMenu.Trigger class="auto-more" aria-label="More" title="More"
              ><Icon name="dots-three" size={16} /></DropdownMenu.Trigger
            >
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                class="auto-menu"
                data-menu
                data-surface="float"
                align="end"
                sideOffset={4}
              >
                <DropdownMenu.Item data-menu-row>
                  {#snippet child({ props })}
                    <a {...props} href={resolve('/automations/[id]', { id: automation.id })}
                      ><span data-menu-lead><Icon name="rename" size={14} /></span>Edit</a
                    >
                  {/snippet}
                </DropdownMenu.Item>
                <DropdownMenu.Item
                  data-menu-row
                  onSelect={async () => {
                    await source.runAutomation(automation.id);
                    await load();
                  }}
                >
                  <span data-menu-lead><Icon name="lightning" size={14} /></span>Run now
                </DropdownMenu.Item>
                <DropdownMenu.Separator data-menu-separator />
                <DropdownMenu.Item data-menu-row onSelect={() => (deleting = automation)}>
                  <span data-menu-lead><Icon name="trash" size={14} /></span>Delete
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
          <Switch
            on={automation.active}
            label={automation.name}
            onchange={(next) => setActive(automation, next)}
          />
        </li>
      {/each}
    </ul>
  {/if}
</div>

<ConfirmDialog
  open={deleting !== undefined}
  title="Delete automation?"
  message="This will delete {deleting?.name}. You can undo it straight after."
  onconfirm={remove}
  oncancel={() => (deleting = undefined)}
/>

<style>
  .automations {
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
    padding-block: 4px;
    margin-block-end: 4px;
  }
  .title {
    display: flex;
    gap: 6px;
    padding-inline: 4px;
  }
  .count {
    color: var(--color-gray-500);
  }
  .create {
    padding: 4px 10px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    font-size: var(--text-caption);
    line-height: 16px;
  }
  :global([data-theme='dark']) .create {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
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
    gap: 12px;
    padding-inline-start: 4px;
    min-inline-size: 0;
  }
  .search input {
    inline-size: 100%;
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
  .status {
    background: transparent;
    color: var(--color-gray-700);
    font-size: 13px;
  }
  :global(.auto-menu) {
    z-index: 9999;
    min-inline-size: 170px;
  }
  :global(.auto-more) {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    border-radius: 8px;
    color: var(--color-gray-400);
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
  }
  .empty-hint {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .rows {
    display: grid;
    gap: 2px;
    margin-block-start: 4px;
  }
  .row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-block-size: 32px;
    padding: 4px 8px;
    border-radius: 12px;
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
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .row:hover .name {
    text-decoration: underline;
  }
  :global([data-theme='dark']) .name {
    color: var(--color-gray-200);
  }
  .schedule {
    color: var(--color-gray-500);
    font-size: 11px;
  }
  .next {
    color: var(--color-gray-400);
    font-size: 11px;
  }
  :is(.create, .main, .undo button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
