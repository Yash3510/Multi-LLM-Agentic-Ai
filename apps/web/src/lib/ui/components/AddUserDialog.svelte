<script lang="ts">
  // Add people (admin look §7, F28 to F36): one by hand, or many from a CSV file. Passwords go
  // straight to the data source and are never logged or kept here after saving.
  import { Dialog } from 'bits-ui';
  import type { DataSource, User } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { readPeopleCsv, TEMPLATE } from '$lib/ui/people-csv';
  import SecretInput from './SecretInput.svelte';
  import './admin-dialog.css';
  import './modal.css';

  type Props = {
    open: boolean;
    source: DataSource;
    onsaved: () => void;
    onclose: () => void;
  };

  let { open, source, onsaved, onclose }: Props = $props();

  let tab = $state<'form' | 'csv'>('form');
  let role = $state<User['role']>('user');
  let name = $state('');
  let email = $state('');
  let password = $state('');
  let file = $state<File>();
  let picker = $state<HTMLInputElement>();
  let busy = $state(false);
  let problems = $state<string[]>([]);
  let notice = $state('');

  // Each opening starts with empty fields and the user role; the tab stays as it was.
  $effect(() => {
    if (!open) return;
    role = 'user';
    name = email = password = '';
    file = undefined;
    problems = [];
    notice = '';
  });

  async function saveOne() {
    try {
      await source.addUser({ name, email, password, role });
      password = '';
      onsaved();
    } catch (error) {
      problems = [error instanceof Error ? error.message : 'The person was not added.'];
    }
  }

  async function importFile() {
    if (!file) {
      problems = ['File not found.'];
      return;
    }
    const { people, problems: bad } = readPeopleCsv(await file.text());
    const failed: string[] = [];
    let added = 0;
    // Ten at a time, as the running app does.
    for (let start = 0; start < people.length; start += 10) {
      const results = await Promise.allSettled(
        people.slice(start, start + 10).map((person) => source.addUser(person)),
      );
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') added += 1;
        else
          failed.push(
            `Row ${start + index + 2}: ${result.reason instanceof Error ? result.reason.message : 'not added.'}`,
          );
      });
    }
    problems = [...bad, ...failed];
    notice = `Successfully imported ${added} users.`;
    file = undefined;
    if (added) onsaved();
  }

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (busy) return;
    busy = true;
    problems = [];
    notice = '';
    try {
      await (tab === 'form' ? saveOne() : importFile());
    } finally {
      busy = false;
    }
  }

  function downloadTemplate() {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([TEMPLATE], { type: 'text/csv' }));
    link.download = 'user-import-template.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog small">
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}<h3 {...props} class="title">Add User</h3>{/snippet}
          </Dialog.Title>
          <Dialog.Close class="close" aria-label="Close"><Icon name="x" size={16} /></Dialog.Close>
        </div>
        <form class="body" onsubmit={submit}>
          <div class="tabs">
            <button type="button" aria-pressed={tab === 'form'} onclick={() => (tab = 'form')}
              >Form</button
            >
            <button type="button" aria-pressed={tab === 'csv'} onclick={() => (tab = 'csv')}
              >CSV Import</button
            >
          </div>
          <div class="fields">
            {#if tab === 'form'}
              <label>
                <span class="label">Role</span>
                <span class="select">
                  <select class="plain" bind:value={role} aria-label="Role" required>
                    <option value="pending">pending</option>
                    <option value="user">user</option>
                    <option value="admin">admin</option>
                  </select>
                  <Icon name="caret-down" size={16} />
                </span>
              </label>
              <label class="gap">
                <span class="label">Name</span>
                <input
                  class="plain"
                  bind:value={name}
                  placeholder="Enter Your Full Name"
                  autocomplete="off"
                  required
                />
              </label>
              <div class="divider"></div>
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
                <span class="label">Password</span>
                <SecretInput
                  bind:value={password}
                  label="Password"
                  placeholder="Enter Your Password"
                  autocomplete="new-password"
                  required
                />
              </div>
            {:else}
              <input
                bind:this={picker}
                type="file"
                accept=".csv"
                hidden
                aria-label="CSV file"
                onchange={(event) => (file = event.currentTarget.files?.[0])}
              />
              <button type="button" class="drop" onclick={() => picker?.click()}>
                {file ? '1 document(s) selected.' : 'Click here to select a csv file.'}
              </button>
              <p class="help">
                <Icon name="info" size={12} /> Ensure your CSV file includes 4 columns in this order:
                Name, Email, Password, Role.
                <button type="button" class="template" onclick={downloadTemplate}
                  >Click here to download user import template file.</button
                >
              </p>
            {/if}
            {#each problems as problem (problem)}<p class="problem" role="alert">
                {problem}
              </p>{/each}
            {#if notice}<p class="notice" role="status">{notice}</p>{/if}
          </div>
          <div class="footer">
            <button type="submit" class="pill" disabled={busy}>Save</button>
          </div>
        </form>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .body {
    padding: 0 16px 12px;
  }

  .tabs {
    display: flex;
    gap: 4px;
    margin-block: -8px 6px;
    font-size: var(--text-ui);
  }

  .tabs button {
    padding: 6px;
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

  .fields {
    display: flex;
    flex-direction: column;
    padding-inline: 4px;
  }

  /* Gaps as the running app measures them: 7 px from a label to its field, 13 px from Role to
     Name, 11 px above the divider and 5 px above Password, whose row is 24 px tall. */
  label,
  .gap {
    display: block;
  }

  .fields :global(.label) {
    margin-block-end: 7px;
  }

  .gap {
    margin-block-start: 13px;
  }

  .fields :global(.divider) {
    margin-block-start: 11px;
  }

  .password {
    margin-block-start: 5px;
  }

  .password :global(.label) {
    margin-block-end: 4px;
  }

  .password :global(.secret) {
    block-size: 24px;
  }

  .drop {
    inline-size: 100%;
    padding-block: 12px;
    border: 1px dashed var(--color-gray-200);
    border-radius: 12px;
    font-size: var(--text-ui);
    text-align: center;
    transition: background-color 150ms;
  }

  .drop:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .drop {
    border-color: var(--color-gray-850);
  }

  :global([data-theme='dark']) .drop:hover {
    background-color: var(--color-gray-850);
  }

  .help {
    margin-block-start: 12px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .template {
    text-decoration: underline;
  }

  :global([data-theme='dark']) .template {
    color: var(--color-gray-200);
  }

  .notice {
    margin-block-start: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  :is(.tabs button, .drop, .template):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
