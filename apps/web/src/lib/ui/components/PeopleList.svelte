<script lang="ts">
  // The admin People list (admin look §5, F9 to F27): search, Add User, and the table of people
  // with their role, email, last activity and join date. Deleting needs the person's email typed
  // in, and can be undone straight after; every change lands in the admin ledger.
  import type { AdminUser, DataSource } from '$lib/data';
  import { ago } from '$lib/ui/ago';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { Dialog } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { ChatSummary } from '$lib/data';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import './modal.css';
  import './admin-dialog.css';

  type Props = {
    source: DataSource;
    /** Opens the add dialog. */
    onadd?: () => void;
    /** Opens the edit dialog for a person. */
    onedit?: (person: AdminUser) => void;
    /** Opens the access preview for a person. */
    onpreview?: (person: AdminUser) => void;
    /** Bumped by the page to reload after a dialog saves. */
    version?: number;
  };

  let { source, onadd, onedit, onpreview, version = 0 }: Props = $props();

  type Column = 'name' | 'role' | 'email' | 'lastActive' | 'created';
  const COLUMNS: [Column, string][] = [
    ['name', 'Name'],
    ['role', 'Role'],
    ['email', 'Email'],
    ['lastActive', 'Last Active'],
    ['created', 'Created at'],
  ];

  let people = $state<AdminUser[]>();
  let query = $state('');
  let sort = $state<{ column: Column; ascending: boolean }>({
    column: 'created',
    ascending: true,
  });
  let deleting = $state<AdminUser>();
  let typed = $state('');
  let undo = $state<AdminUser>();
  let now = $state(new Date());
  let pageIndex = $state(0);
  let chatsOf = $state<{ person: AdminUser; chats: ChatSummary[] }>();
  const PER_PAGE = 30;

  async function showChats(person: AdminUser) {
    chatsOf = { person, chats: await source.userChats(person.id) };
  }

  const initials = (name: string) =>
    name
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join('');

  async function load() {
    people = await source.listUsers();
    now = new Date();
  }

  $effect(() => {
    void version;
    void load();
  });

  const shown = $derived.by(() => {
    const value = query.trim().toLowerCase();
    const sign = sort.ascending ? 1 : -1;
    return (people ?? [])
      .filter(
        (one) => one.name.toLowerCase().includes(value) || one.email.toLowerCase().includes(value),
      )
      .sort((a, b) => {
        const [x, y] = [a[sort.column], b[sort.column]];
        return (
          sign *
          (x instanceof Date && y instanceof Date
            ? x.getTime() - y.getTime()
            : String(x).localeCompare(String(y)))
        );
      });
  });

  const joined = new Intl.DateTimeFormat('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
  const roleLabel = (role: string) => role.charAt(0).toUpperCase() + role.slice(1);
  const online = (person: AdminUser) => now.getTime() - person.lastActive.getTime() < 180_000;

  function sortBy(column: Column) {
    sort = { column, ascending: sort.column === column ? !sort.ascending : true };
  }

  async function remove() {
    if (!deleting) return;
    const person = deleting;
    deleting = undefined;
    typed = '';
    await source.deleteUser(person.id);
    undo = person;
    await load();
  }

  async function restore() {
    if (!undo) return;
    await source.restoreUser(undo.id);
    undo = undefined;
    await load();
  }
</script>

<div class="people">
  {#if !people}
    <p class="loading" aria-busy="true">Loading…</p>
  {:else}
    <div class="toolbar">
      <label class="search">
        <Icon name="magnifying-glass" size={14} />
        <input bind:value={query} placeholder="Search" aria-label="Search" />
        {#if query}
          <button type="button" class="clear" aria-label="Clear search" onclick={() => (query = '')}
            ><Icon name="x-bold" size={12} /></button
          >
        {/if}
      </label>
      <button type="button" class="add" onclick={onadd}>Add User</button>
    </div>
    {#if undo}
      <p class="undo" role="status">
        Deleted {undo.name}.
        <button type="button" onclick={restore}>Undo</button>
      </p>
    {/if}
    <div class="scroller">
      <table>
        <thead>
          <tr>
            {#each COLUMNS as [column, label] (column)}
              <th
                aria-sort={sort.column === column
                  ? sort.ascending
                    ? 'ascending'
                    : 'descending'
                  : 'none'}
              >
                <button type="button" onclick={() => sortBy(column)}>
                  {label}
                  <span class="caret" class:hidden={sort.column !== column} aria-hidden="true">
                    <Icon
                      name={sort.ascending || sort.column !== column ? 'caret-up' : 'caret-down'}
                      size={8}
                    />
                  </span>
                </button>
              </th>
            {/each}
            <th class="actions-head"><span class="sr-only">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          {#each shown.slice(pageIndex * PER_PAGE, (pageIndex + 1) * PER_PAGE) as person (person.id)}
            <tr>
              <td class="name">
                <span class="who">
                  <span class="avatar" aria-hidden="true"
                    >{#if person.avatar === 'initials'}<span class="initials"
                        >{initials(person.name)}</span
                      >{:else}<Icon name="user" size={14} />{/if}</span
                  >
                  <span class="text">{person.name}</span>
                  {#if online(person)}<span class="online" title="Online"></span>{/if}
                </span>
              </td>
              <td class="role">
                <button
                  type="button"
                  data-role={person.role}
                  aria-label="Change User Role: {roleLabel(person.role)}"
                  onclick={() => onedit?.(person)}>{roleLabel(person.role)}</button
                >
              </td>
              <td class="email"><span class="text">{person.email}</span></td>
              <td>{ago(person.lastActive, now)}</td>
              <td>{joined.format(person.created)}</td>
              <td class="actions">
                <span class="buttons">
                  {#if person.role !== 'admin'}
                    <button
                      type="button"
                      aria-label="Chats"
                      title="Chats"
                      onclick={() => showChats(person)}
                      ><Icon name="chats-circle" size={14} /></button
                    >
                  {/if}
                  {#if person.role !== 'admin'}
                    <button
                      type="button"
                      aria-label="Preview Access"
                      title="Preview Access"
                      onclick={() => onpreview?.(person)}><Icon name="eye" size={14} /></button
                    >
                  {/if}
                  <button
                    type="button"
                    aria-label="Edit User"
                    title="Edit User"
                    onclick={() => onedit?.(person)}><Icon name="pencil-line" size={14} /></button
                  >
                  {#if person.role !== 'admin'}
                    <button
                      type="button"
                      aria-label="Delete User"
                      title="Delete User"
                      onclick={() => (deleting = person)}
                      ><Icon name="trash-simple" size={14} /></button
                    >
                  {/if}
                </span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    {#if shown.length > PER_PAGE}
      <nav class="pager" aria-label="Pages">
        {#each Array.from({ length: Math.ceil(shown.length / PER_PAGE) }, (_, at) => at) as at (at)}
          <button
            type="button"
            aria-current={at === pageIndex ? 'page' : undefined}
            onclick={() => (pageIndex = at)}>{at + 1}</button
          >
        {/each}
      </nav>
    {/if}
    <p class="hint">
      <Icon name="info" size={12} /> Click on the user role button to change a user's role.
    </p>
  {/if}
</div>

<Dialog.Root open={chatsOf !== undefined} onOpenChange={(next) => !next && (chatsOf = undefined)}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog large">
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}
              <h3 {...props} class="title">
                {chatsOf?.person.name.slice(0, 32)}'s Chats
                <span class="muted">{chatsOf?.chats.length}</span>
              </h3>
            {/snippet}
          </Dialog.Title>
          <Dialog.Close class="close" aria-label="Close"><Icon name="x" size={16} /></Dialog.Close>
        </div>
        <div class="chats-body">
          {#each chatsOf?.chats ?? [] as chat (chat.id)}
            <a class="chat-row" href={resolve('/c/[id]', { id: chat.id })}
              >{chat.title}<span>{ago(chat.updated, now)}</span></a
            >
          {:else}
            <p class="chats-none">This person has no chats.</p>
          {/each}
        </div>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<ConfirmDialog
  open={deleting !== undefined}
  title="Delete {deleting?.name ?? 'user'}?"
  message="This removes their account. Type their email to confirm."
  confirmLabel="Delete"
  confirmDisabled={typed.trim().toLowerCase() !== deleting?.email.toLowerCase()}
  onconfirm={remove}
  oncancel={() => {
    deleting = undefined;
    typed = '';
  }}
>
  <input class="typed" bind:value={typed} placeholder={deleting?.email} aria-label="Email" />
</ConfirmDialog>

<style>
  .people {
    font-size: var(--text-ui);
  }

  .loading {
    margin-block: 40px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  .toolbar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 8px;
    block-size: 32px;
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .toolbar {
    background-color: var(--color-gray-900);
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
    padding-inline-end: 16px;
    border-start-end-radius: 12px;
    border-end-end-radius: 12px;
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
    margin-inline-start: 6px;
    padding: 2px;
    border-radius: var(--radius-pill);
    transition: background-color 150ms;
  }

  .clear:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .clear:hover {
    background-color: var(--color-gray-900);
  }

  .add {
    flex-shrink: 0;
    margin-inline-start: 4px;
    padding: 4px 10px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-50);
    box-shadow:
      var(--gloss-edge),
      0 0 0 1px var(--color-gray-200);
    color: var(--color-gray-900);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: background-color 150ms;
    background-image: var(--gloss-fill);
  }

  .add:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .add {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
    color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .add:hover {
    background-color: var(--color-gray-800);
  }

  .undo {
    display: flex;
    gap: 8px;
    margin-block: 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .undo button {
    color: var(--color-gray-900);
    text-decoration: underline;
  }

  :global([data-theme='dark']) .undo button {
    color: var(--color-white);
  }

  .scroller {
    max-inline-size: 100%;
    overflow-x: auto;
    scrollbar-width: none;
    white-space: nowrap;
  }

  table {
    inline-size: 100%;
    color: var(--color-gray-500);
    font-size: var(--text-ui);
    text-align: start;
  }

  :global([data-theme='dark']) table {
    color: var(--color-gray-400);
  }

  thead {
    border-block-end: 1.5px solid var(--color-gray-50);
    color: var(--color-gray-800);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) thead {
    border-color: color-mix(in srgb, var(--color-gray-850) 30%, transparent);
    color: var(--color-gray-200);
  }

  th {
    font-weight: 400;
    text-align: start;
    user-select: none;
  }

  th button {
    display: flex;
    align-items: center;
    gap: 6px;
    inline-size: 100%;
    padding: 6px 10px;
    line-height: 16px;
  }

  .caret {
    display: inline-flex;
  }

  .caret.hidden {
    visibility: hidden;
  }

  .actions-head {
    padding: 6px 10px;
  }

  td {
    padding: 4px 12px;
    font-size: var(--text-caption);
    font-weight: 400;
  }

  .name {
    max-inline-size: 192px;
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .name {
    color: var(--color-white);
  }

  .who {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .avatar {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 22px;
    block-size: 22px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-200);
    color: var(--color-white);
  }

  .text {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .online {
    position: relative;
    flex-shrink: 0;
    inline-size: 6px;
    block-size: 6px;
    border-radius: var(--radius-pill);
    background-color: var(--color-green-500);
  }

  .online::after {
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background-color: color-mix(in srgb, var(--color-green-400) 75%, transparent);
    animation: ping 1s cubic-bezier(0, 0, 0.2, 1) infinite;
    content: '';
  }

  /* The running app's ping doubles the ring; growing its box keeps within the scale cap. */
  @keyframes ping {
    75%,
    100% {
      inset: -3px;
      opacity: 0;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .online::after {
      animation: none;
    }
  }

  .role {
    inline-size: 80px;
    min-inline-size: 80px;
  }

  .role button {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: color 150ms;
  }

  .role button[data-role='admin'] {
    color: var(--color-role-admin);
  }

  .role button[data-role='user'] {
    color: var(--color-role-user);
  }

  :global([data-theme='dark']) .role button[data-role='pending'] {
    color: var(--color-gray-400);
  }

  .email {
    max-inline-size: 192px;
  }

  .actions {
    text-align: end;
  }

  .buttons {
    display: inline-flex;
    justify-content: flex-end;
  }

  .buttons button {
    display: grid;
    padding: 6px;
    border-radius: 8px;
    transition: background-color 150ms;
  }

  .buttons button:hover {
    background-color: rgb(0 0 0 / 0.05);
  }

  :global([data-theme='dark']) .buttons button:hover {
    background-color: rgb(255 255 255 / 0.05);
  }

  .hint {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 4px;
    /* 6 px in the spec; the running app's table ends 3 px higher than ours. */
    margin-block-start: 3px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .initials {
    color: var(--color-gray-700);
    font-size: 9px;
  }
  .pager {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-block: 8px;
  }
  .pager button {
    inline-size: 32px;
    block-size: 32px;
    border-radius: 9px;
    font-size: var(--text-ui);
  }
  .pager button:hover,
  .pager button[aria-current] {
    background-color: var(--color-gray-50);
  }
  :global([data-theme='dark']) .pager button[aria-current] {
    background-color: var(--color-gray-850);
  }
  .muted {
    margin-inline-start: 8px;
    color: var(--color-gray-500);
  }
  .chats-body {
    max-block-size: 352px;
    padding: 0 20px 16px;
    overflow-y: auto;
  }
  .chat-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: var(--text-ui);
  }
  .chat-row span {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .chat-row:hover {
    background-color: color-mix(in srgb, var(--color-gray-50) 70%, transparent);
  }
  .chats-none {
    min-block-size: 80px;
    padding: 20px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }
  .typed {
    inline-size: 100%;
    margin-block-start: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    font-size: var(--text-ui);
  }

  .typed:focus {
    outline: none;
  }

  :global([data-theme='dark']) .typed {
    background-color: var(--color-gray-900);
    color: var(--color-gray-300);
  }

  :is(.clear, .add, .undo button, th button, .role button, .buttons button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
