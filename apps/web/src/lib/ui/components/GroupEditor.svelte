<script lang="ts">
  // The group editor (admin look §12, F64 to F92): one dialog to add a group, edit one (General,
  // Permissions, Users, Preview) or edit the default permissions (Permissions only). Members
  // change at once; deleting needs the group's name typed in. Every change lands in the ledger.
  import { Dialog } from 'bits-ui';
  import type { AdminUser, DataSource, Group, StoredPermissions } from '$lib/data';
  import { ago } from '$lib/ui/ago';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { DEFAULT_PERMISSIONS, fillPermissions, type Permissions } from '$lib/ui/permissions';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import PermissionsPanel from './PermissionsPanel.svelte';
  import './admin-dialog.css';
  import './modal.css';

  type Mode = 'create' | 'edit' | 'defaults';
  type Props = {
    open: boolean;
    source: DataSource;
    mode: Mode;
    group?: Group;
    /** The stored default permissions. */
    defaults: StoredPermissions;
    onsaved: () => void;
    ondeleted?: (group: Group) => void;
    onclose: () => void;
  };

  let { open, source, mode, group, defaults, onsaved, ondeleted, onclose }: Props = $props();

  type Tab = 'general' | 'permissions' | 'users' | 'preview';
  const TABS: Record<Mode, Tab[]> = {
    create: ['general', 'permissions'],
    edit: ['general', 'permissions', 'users', 'preview'],
    defaults: ['permissions'],
  };
  const LABELS: Record<Tab, [string, IconName]> = {
    general: ['General', 'gear-six'],
    permissions: ['Permissions', 'wrench-bold'],
    users: ['Users', 'user-plus-bold'],
    preview: ['Preview', 'eye'],
  };
  const TITLES: Record<Mode, string> = {
    create: 'Add User Group',
    edit: 'Edit User Group',
    defaults: 'Edit Default Permissions',
  };

  let tab = $state<Tab>('general');
  let name = $state('');
  let description = $state('');
  let share = $state<Group['share']>('members');
  let permissions = $state<Permissions>(fillPermissions({}));
  let members = $state<string[]>([]);
  let people = $state<AdminUser[]>([]);
  let query = $state('');
  let access = $state<Awaited<ReturnType<DataSource['previewAccess']>>>();
  let busy = $state(false);
  let resetting = $state(false);
  let deleting = $state(false);
  let typed = $state('');

  // Each opening starts on the first tab with the group (or defaults) copied in.
  $effect(() => {
    if (!open) return;
    tab = TABS[mode][0];
    name = group?.name ?? '';
    description = group?.description ?? '';
    share = group?.share ?? 'members';
    members = [...(group?.members ?? [])];
    permissions = fillPermissions(
      mode === 'defaults' ? defaults : mode === 'create' ? defaults : (group?.permissions ?? {}),
    );
    query = '';
  });

  $effect(() => {
    if (open && tab === 'users') void source.listUsers().then((loaded) => (people = loaded));
    if (open && tab === 'preview' && group) {
      access = undefined;
      void source.previewAccess(group.id).then((loaded) => (access = loaded));
    }
  });

  const shownPeople = $derived(
    people
      .filter((one) =>
        `${one.name} ${one.email}`.toLowerCase().includes(query.trim().toLowerCase()),
      )
      .sort((a, b) => Number(members.includes(b.id)) - Number(members.includes(a.id))),
  );

  async function save(event: SubmitEvent) {
    event.preventDefault();
    if (busy) return;
    busy = true;
    try {
      const stored = $state.snapshot(permissions);
      if (mode === 'defaults') await source.saveDefaultPermissions(stored);
      else if (mode === 'create')
        await source.createGroup({ name, description, share, permissions: stored });
      else if (group)
        await source.updateGroup(group.id, { name, description, share, permissions: stored });
      onsaved();
    } finally {
      busy = false;
    }
  }

  async function toggle(person: AdminUser, member: boolean) {
    if (!group) return;
    await source.setGroupMember(group.id, person.id, member);
    members = member ? [...members, person.id] : members.filter((one) => one !== person.id);
  }

  async function remove() {
    if (!group) return;
    deleting = false;
    typed = '';
    await source.deleteGroup(group.id);
    ondeleted?.(group);
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog large">
        <div class="head editor-head">
          <Dialog.Title>
            {#snippet child({ props })}<h3 {...props} class="title">{TITLES[mode]}</h3>{/snippet}
          </Dialog.Title>
          <Dialog.Close class="close" aria-label="Close"><Icon name="x" size={16} /></Dialog.Close>
        </div>
        <form class="body" onsubmit={save}>
          <div class="tabs">
            {#each TABS[mode] as one (one)}
              <button type="button" aria-pressed={tab === one} onclick={() => (tab = one)}>
                <Icon name={LABELS[one][1]} size={16} />{LABELS[one][0]}
              </button>
            {/each}
          </div>
          <div class="pane">
            <div class="scroll">
              {#if tab === 'general'}
                <div class="general">
                  <label>
                    <span class="label">Name</span>
                    <input class="plain" bind:value={name} placeholder="Group Name" required />
                  </label>
                  <label>
                    <span class="label">Description</span>
                    <textarea
                      class="plain"
                      bind:value={description}
                      placeholder="Group Description"
                      rows="1"></textarea>
                  </label>
                  <div class="divider"></div>
                  <div>
                    <span class="label">Setting</span>
                    <div class="setting">
                      <span>Who can share to this group</span>
                      <select
                        class="share"
                        bind:value={share}
                        aria-label="Who can share to this group"
                      >
                        <option value="none">No one</option>
                        <option value="members">Members</option>
                        <option value="anyone">Anyone</option>
                      </select>
                    </div>
                  </div>
                  {#if mode === 'edit'}
                    <div>
                      <span class="label">Actions</span>
                      <button type="button" class="delete" onclick={() => (deleting = true)}
                        >Delete</button
                      >
                    </div>
                  {/if}
                </div>
              {:else if tab === 'permissions'}
                <PermissionsPanel
                  bind:permissions
                  defaults={mode === 'edit' ? defaults : undefined}
                />
              {:else if tab === 'users'}
                <label class="member-search">
                  <Icon name="magnifying-glass" size={16} />
                  <input bind:value={query} placeholder="Search" aria-label="Search" />
                </label>
                {#if shownPeople.length}
                  <table>
                    <thead>
                      <tr><th class="mbr">MBR</th><th>Name</th><th>Role</th><th>Last Active</th></tr
                      >
                    </thead>
                    <tbody>
                      {#each shownPeople as person (person.id)}
                        <tr>
                          <td class="mbr">
                            <input
                              type="checkbox"
                              aria-label={person.name}
                              checked={members.includes(person.id)}
                              onchange={(event) => toggle(person, event.currentTarget.checked)}
                            />
                          </td>
                          <td class="who" title={person.email}>{person.name}</td>
                          <td data-role={person.role} class="role">{person.role}</td>
                          <td>{ago(person.lastActive)}</td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                {:else}
                  <p class="none">No users were found.</p>
                {/if}
              {:else if tab === 'preview'}
                {#if !access}
                  <p class="none" aria-busy="true">Loading…</p>
                {:else}
                  {#each [['Models', access.models, 'No models accessible'], ['Knowledge', access.knowledge, 'No knowledge bases accessible'], ['Tools', access.tools, 'No tools accessible']] as const as [heading, items, empty], index (heading)}
                    {#if index}<div class="divider"></div>{/if}
                    <h4>{heading}</h4>
                    {#each items as item, at (at)}<p class="item">{item}</p>{:else}<p class="none">
                        {empty}
                      </p>{/each}
                  {/each}
                {/if}
              {/if}
            </div>
            {#if tab === 'general' || tab === 'permissions'}
              <div class="footer editor-footer">
                {#if tab === 'permissions'}
                  <button
                    type="button"
                    class="reset"
                    title={mode === 'defaults'
                      ? 'Reset to the built-in default permissions.'
                      : 'Reset to the current default user permissions.'}
                    onclick={() => (resetting = true)}>Reset to Defaults</button
                  >
                {:else}
                  <span></span>
                {/if}
                <button type="submit" class="pill" disabled={busy}>Save</button>
              </div>
            {/if}
          </div>
        </form>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<ConfirmDialog
  open={resetting}
  title="Reset to Defaults"
  message="All permissions go back to their defaults. You still need to save."
  onconfirm={() => {
    permissions =
      mode === 'defaults' ? structuredClone(DEFAULT_PERMISSIONS) : fillPermissions(defaults);
    resetting = false;
  }}
  oncancel={() => (resetting = false)}
/>

<ConfirmDialog
  open={deleting}
  title="Delete {group?.name ?? 'group'}?"
  message="This removes the group. Type its name to confirm."
  confirmLabel="Delete"
  confirmDisabled={typed.trim() !== group?.name}
  onconfirm={remove}
  oncancel={() => {
    deleting = false;
    typed = '';
  }}
>
  <input class="typed" bind:value={typed} placeholder={group?.name} aria-label="Group name" />
</ConfirmDialog>

<style>
  :global(.admin-dialog.large) {
    inline-size: 896px;
  }

  :global([data-theme='dark']) .editor-head {
    color: var(--color-gray-100);
  }

  .body {
    display: flex;
    flex-direction: column;
    padding: 0 16px 16px;
  }

  @media (min-width: 64rem) {
    .body {
      flex-direction: row;
      gap: 16px;
      /* 8 px under the form and 16 px round the body, as the running app. */
      padding-block-end: 24px;
    }
  }

  .tabs {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    scrollbar-width: none;
    font-size: var(--text-ui);
  }

  @media (min-width: 64rem) {
    .tabs {
      flex: none;
      flex-direction: column;
      gap: 4px;
      inline-size: 160px;
    }
  }

  .tabs button {
    display: flex;
    align-items: center;
    gap: 8px;
    max-inline-size: fit-content;
    padding: 4px 2px;
    border-radius: 8px;
    color: var(--color-gray-300);
    transition: color 150ms;
  }

  .tabs button:hover {
    color: var(--color-gray-700);
  }

  .tabs button[aria-pressed='true'] {
    color: inherit;
  }

  :global([data-theme='dark']) .tabs button {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .tabs button:hover {
    color: var(--color-white);
  }

  :global([data-theme='dark']) .tabs button[aria-pressed='true'] {
    color: inherit;
  }

  .pane {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
    margin-block-start: 4px;
  }

  @media (min-width: 64rem) {
    .pane {
      block-size: 480px;
    }
  }

  .scroll {
    flex: 1;
    overflow-y: auto;
    scrollbar-width: none;
  }

  .general {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .general :global(.label) {
    margin-block-end: 2px;
  }

  .general textarea {
    resize: none;
    field-sizing: content;
  }

  .general .divider {
    margin-block: 4px;
  }

  .setting {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: var(--text-caption);
  }

  .share {
    padding: 4px 8px;
    border-radius: 8px;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    text-align: end;
  }

  .delete {
    font-size: var(--text-caption);
  }

  .delete:hover {
    text-decoration: underline;
  }

  .member-search {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-block-end: 6px;
  }

  .member-search input {
    flex: 1;
    background: transparent;
    font-size: var(--text-ui);
  }

  .member-search input:focus {
    outline: none;
  }

  table {
    inline-size: 100%;
    color: var(--color-gray-500);
    text-align: start;
  }

  thead {
    border-block-end: 1.5px solid color-mix(in srgb, var(--color-gray-50) 50%, transparent);
    font-size: var(--text-caption);
  }

  th {
    padding: 6px 10px;
    font-weight: 400;
    text-align: start;
  }

  td {
    padding: 4px 12px;
    font-size: var(--text-caption);
  }

  .mbr {
    inline-size: 32px;
  }

  .who {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .who {
    color: var(--color-white);
  }

  .role {
    text-transform: capitalize;
  }

  .role[data-role='admin'] {
    color: var(--color-role-admin);
  }

  .role[data-role='user'] {
    color: var(--color-role-user);
  }

  .none {
    padding: 40px 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  h4 {
    margin-block-end: 8px;
    font-size: var(--text-ui);
    font-weight: 400;
  }

  .item {
    margin-block: 4px;
    font-size: var(--text-caption);
  }

  .editor-footer {
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    font-size: var(--text-ui);
  }

  .reset {
    color: var(--color-gray-500);
    transition: color 150ms;
  }

  .reset:hover {
    color: var(--color-gray-700);
    text-decoration: underline;
  }

  :global([data-theme='dark']) .reset:hover {
    color: var(--color-gray-300);
  }

  .typed {
    inline-size: 100%;
    margin-block-start: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    font-size: var(--text-ui);
  }

  :global([data-theme='dark']) .typed {
    background-color: var(--color-gray-900);
    color: var(--color-gray-300);
  }

  :is(.tabs button, .delete, .reset):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
