<script lang="ts">
  // Edit a person (admin look §8, F37 to F44): role, name, email and an optional new password.
  // You cannot change your own role. A new password goes straight to the data source and is never
  // logged or kept here.
  import { Dialog } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { AdminUser, DataSource, Group, User } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import SecretInput from './SecretInput.svelte';
  import './admin-dialog.css';
  import './modal.css';

  type Props = {
    open: boolean;
    source: DataSource;
    person?: AdminUser;
    /** The signed-in admin, whose own role is locked. */
    selfId: string;
    onsaved: () => void;
    onclose: () => void;
  };

  let { open, source, person, selfId, onsaved, onclose }: Props = $props();

  let role = $state<User['role']>('user');
  let name = $state('');
  let email = $state('');
  let password = $state('');
  let avatar = $state<'default' | 'initials'>('default');
  let problem = $state('');
  let groups = $state<Group[]>([]);

  // Each opening copies the person into the form and blanks the password.
  $effect(() => {
    if (!open || !person) return;
    role = person.role;
    avatar = person.avatar ?? 'default';
    name = person.name;
    email = person.email;
    password = '';
    problem = '';
    groups = [];
    void source.userGroups(person.id).then((loaded) => (groups = loaded));
  });

  const joined = new Intl.DateTimeFormat('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!person) return;
    try {
      await source.updateUser(person.id, {
        name,
        email,
        role,
        avatar,
        password: password || undefined,
      });
      password = '';
      onsaved();
    } catch (error) {
      problem = error instanceof Error ? error.message : 'The changes were not saved.';
    }
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog small">
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}<h3 {...props} class="title">Edit User</h3>{/snippet}
          </Dialog.Title>
          <Dialog.Close class="close" aria-label="Close"><Icon name="x" size={16} /></Dialog.Close>
        </div>
        {#if person}
          <form class="body" onsubmit={submit}>
            <div class="top">
              <div class="picture">
                <span class="avatar" aria-hidden="true"
                  >{#if avatar === 'initials'}<span class="initials"
                      >{name
                        .split(/\s+/)
                        .slice(0, 2)
                        .map((part) => part.charAt(0).toUpperCase())
                        .join('')}</span
                    >{:else}<Icon name="user" size={32} />{/if}</span
                >
                <button type="button" class="pic-action" onclick={() => (avatar = 'default')}
                  >Remove</button
                >
                <button type="button" class="pic-action" onclick={() => (avatar = 'initials')}
                  >Initials</button
                >
              </div>
              <div class="details">
                <p class="name">{person.name}</p>
                <p class="created">Created at {joined.format(person.created)}</p>
                <div class="stack">
                  {#if groups.length}
                    <div>
                      <span class="label">User Groups</span>
                      <div class="chips">
                        {#each groups as group (group.id)}
                          <a
                            class="chip"
                            href="{resolve('/admin/users/[tab]', { tab: 'groups' })}?id={group.id}"
                            >{group.name}</a
                          >
                        {/each}
                      </div>
                    </div>
                  {/if}
                  <label>
                    <span class="label">Role</span>
                    <span class="select">
                      <select
                        class="plain"
                        bind:value={role}
                        aria-label="Role"
                        disabled={person.id === selfId}
                      >
                        <option value="admin">Admin</option>
                        <option value="user">User</option>
                        <option value="pending">Pending</option>
                      </select>
                      <Icon name="caret-down" size={16} />
                    </span>
                  </label>
                  <label>
                    <span class="label">Name</span>
                    <input
                      class="plain"
                      bind:value={name}
                      placeholder="Enter Your Name"
                      autocomplete="off"
                      required
                    />
                  </label>
                  <label>
                    <span class="label">Email</span>
                    <input
                      class="plain"
                      type="email"
                      bind:value={email}
                      placeholder="Enter Your Email"
                      autocomplete="off"
                      required
                    />
                  </label>
                  <div class="password">
                    <span class="label">New Password</span>
                    <SecretInput
                      bind:value={password}
                      label="New Password"
                      placeholder="Enter New Password"
                      autocomplete="new-password"
                    />
                  </div>
                </div>
                {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
              </div>
            </div>
            <div class="footer"><button type="submit" class="pill">Save</button></div>
          </form>
        {/if}
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .body {
    padding: 12px 20px 20px;
  }

  .top {
    display: flex;
    gap: 24px;
  }

  .avatar {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 56px;
    block-size: 56px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-300);
    color: var(--color-white);
  }

  .picture {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .initials {
    color: var(--color-gray-700);
    font-size: 18px;
  }
  .pic-action {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .pic-action:first-of-type {
    margin-block-start: 8px;
  }
  .details {
    flex: 1;
    min-inline-size: 0;
  }

  .name {
    overflow: hidden;
    font-size: var(--text-base);
    line-height: 24px;
    text-overflow: ellipsis;
    text-transform: capitalize;
    white-space: nowrap;
  }

  .created {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .stack {
    display: flex;
    flex-direction: column;
    /* Gaps as the running app measures them: 7 px between fields and from a label to its
       field; the password row is 24 px tall, 4 px under its label. */
    gap: 7px;
    margin-block-start: 8px;
  }

  .stack :global(.label) {
    margin-block-end: 7px;
  }

  .password :global(.label) {
    margin-block-end: 4px;
  }

  .password :global(.secret) {
    block-size: 24px;
  }

  label {
    display: block;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin: 2px -4px;
  }

  .chip {
    padding: 2px 6px;
    border-radius: 12px;
    background-color: var(--color-gray-100);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .chip {
    background-color: var(--color-gray-850);
  }
</style>
