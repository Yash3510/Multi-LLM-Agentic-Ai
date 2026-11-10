<script lang="ts">
  // Account (chat-composer look §9.14, F103): the picture (upload, initials or the default), name,
  // bio, gender, birth date and user variables, saved with Save; and the password change. The API
  // keys section is not built: it is switched off on the running app and shows session secrets.
  import { untrack } from 'svelte';
  import type { DataSource, Profile } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import SettingsSelect from './SettingsSelect.svelte';
  import VariableDialog from './VariableDialog.svelte';
  import './settings-page.css';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  let profile = $state<Profile>();
  let gender = $state('');
  let customGender = $state('');
  let variables = $state<{ key: string; value: string }[]>([]);
  let editing = $state<{ index?: number }>();
  let picker = $state<HTMLInputElement>();
  let notice = $state('');

  let showPassword = $state(false);
  let current = $state('');
  let next = $state('');
  let confirm = $state('');
  let passwordNotice = $state('');
  let passwordProblem = $state('');

  const GENDERS = [
    { value: '', label: 'Prefer not to say' },
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'custom', label: 'Custom' },
  ];

  async function load() {
    const loaded = await source.getProfile();
    profile = loaded;
    const saved = loaded.gender ?? '';
    gender = ['', 'male', 'female'].includes(saved) ? saved : 'custom';
    customGender = gender === 'custom' ? saved : '';
    variables = Object.entries(loaded.variables).map(([key, value]) => ({ key, value }));
  }
  untrack(() => void load());

  const initials = $derived(
    (profile?.name ?? '')
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join(''),
  );

  /** A picture, scaled to fit 250 px square where the browser can draw it. */
  async function readPhoto(file: File): Promise<string> {
    const url = await new Promise<string>((done, fail) => {
      const reader = new FileReader();
      reader.onload = () => done(String(reader.result));
      reader.onerror = () => fail(reader.error);
      reader.readAsDataURL(file);
    });
    const image = new Image();
    image.src = url;
    await image.decode();
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (!context) return url;
    const scale = Math.min(1, 250 / Math.max(image.width, image.height));
    canvas.width = Math.round(image.width * scale);
    canvas.height = Math.round(image.height * scale);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/webp', 0.8);
  }

  async function upload(event: Event & { currentTarget: HTMLInputElement }) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    input.value = '';
    if (!profile || !file?.type.startsWith('image/')) return;
    profile.avatar = { kind: 'photo', src: await readPhoto(file) };
  }

  function doneVariable(variable: { key: string; value: string }) {
    const index = editing?.index;
    variables =
      index === undefined
        ? [...variables, variable]
        : variables.map((one, at) => (at === index ? variable : one));
    editing = undefined;
  }

  async function save() {
    if (!profile) return;
    await source.saveProfile({
      ...$state.snapshot(profile),
      gender: gender === 'custom' ? customGender.trim() : gender,
      variables: Object.fromEntries(variables.map((one) => [one.key, one.value])),
    });
    notice = 'Settings saved successfully!';
  }

  async function changePassword() {
    passwordNotice = '';
    passwordProblem = '';
    if (next !== confirm) {
      passwordProblem =
        "The passwords you entered don't quite match. Please double-check and try again.";
      return;
    }
    try {
      await source.changePassword(current, next);
    } catch (error) {
      passwordProblem = error instanceof Error ? error.message : 'The password was not changed.';
      return;
    }
    current = next = confirm = '';
    passwordNotice = 'Password updated.';
  }
</script>

<div class="settings-page">
  <div class="body">
    <h2>Account</h2>
    {#if profile}
      <section>
        <h3>Profile</h3>
        <div class="rows">
          <div class="picture">
            <button
              type="button"
              class="avatar"
              aria-label="Upload Photo"
              onclick={() => picker?.click()}
            >
              {#if profile.avatar.kind === 'photo'}
                <img src={profile.avatar.src} alt="" />
              {:else if profile.avatar.kind === 'initials'}
                <span class="initials">{initials}</span>
              {:else}
                <Icon name="user" size={22} />
              {/if}
              <span class="veil"><Icon name="camera" size={16} /></span>
            </button>
            <input
              bind:this={picker}
              type="file"
              accept="image/*"
              hidden
              aria-label="Profile photo"
              onchange={upload}
            />
            <div class="who">
              <span class="name">{profile.name}</span>
              <span class="links">
                <button type="button" onclick={() => picker?.click()}>Upload Photo</button>
                <span class="dot" aria-hidden="true">·</span>
                <button
                  type="button"
                  onclick={() => profile && (profile.avatar = { kind: 'default' })}>Remove</button
                >
                <span class="dot" aria-hidden="true">·</span>
                <button
                  type="button"
                  onclick={() => profile && (profile.avatar = { kind: 'initials' })}
                  >Initials</button
                >
              </span>
            </div>
          </div>

          <div>
            <span class="field-label">Name</span>
            <div class="field-control">
              <input
                class="input"
                bind:value={profile.name}
                aria-label="Name"
                placeholder="Enter your name"
                required
              />
            </div>
            <p class="note field-note">Set the display name shown across your account.</p>
          </div>
          <div>
            <span class="field-label">Bio</span>
            <div class="field-control">
              <textarea
                class="area bio"
                bind:value={profile.bio}
                aria-label="Bio"
                placeholder="Share your background and interests"
                rows="3"></textarea>
            </div>
            <p class="note field-note">
              Add optional profile context visible where profiles are shown.
            </p>
          </div>
          <div>
            <span class="field-label">Gender</span>
            <div class="field-control">
              <SettingsSelect
                label="Gender"
                value={gender}
                options={GENDERS}
                onchange={(value) => (gender = value)}
                wide
              />
              {#if gender === 'custom'}
                <input
                  class="input custom"
                  bind:value={customGender}
                  aria-label="Custom Gender"
                  placeholder="Enter your gender"
                />
              {/if}
            </div>
            <p class="note field-note">Choose the gender value stored on your profile.</p>
          </div>
          <div>
            <span class="field-label">Birth Date</span>
            <div class="field-control">
              <input
                class="input"
                type="date"
                bind:value={profile.birthDate}
                aria-label="Birth Date"
              />
            </div>
            <p class="note field-note">Set the birth date saved with your profile.</p>
          </div>
        </div>
      </section>

      <section class="variables">
        <div class="variables-head">
          <span>User Variables <span class="count">{variables.length}</span></span>
          <button type="button" class="quiet" onclick={() => (editing = {})}>Add</button>
        </div>
        <div class="variable-list">
          {#each variables as variable, index (variable.key)}
            <div class="variable">
              <span class="key">{variable.key}</span>
              <span class="value">{variable.value || 'Empty'}</span>
              <button type="button" class="quiet" onclick={() => (editing = { index })}>Edit</button
              >
            </div>
          {:else}
            <p class="empty">No user variables configured.</p>
          {/each}
        </div>
        <p class="note usage">
          Use these in model system prompts as {'{{user.variables.key_name}}'}.
        </p>
      </section>

      <section>
        <h3>Password</h3>
        <div class="block">
          <div class="row">
            <span>Change Password</span>
            <button type="button" class="quiet" onclick={() => (showPassword = !showPassword)}
              >{showPassword ? 'Hide' : 'Show'}</button
            >
          </div>
          <p class="note password-note">Update the password used for email and password sign-in.</p>
        </div>
        {#if showPassword}
          <form
            class="password"
            onsubmit={(event) => {
              event.preventDefault();
              void changePassword();
            }}
          >
            <label class="secret">
              <span>Current Password</span>
              <input
                class="input"
                type="password"
                bind:value={current}
                placeholder="Enter your current password"
                autocomplete="current-password"
                required
              />
            </label>
            <label class="secret">
              <span>New Password</span>
              <input
                class="input"
                type="password"
                bind:value={next}
                placeholder="Enter your new password"
                autocomplete="new-password"
                required
              />
            </label>
            <label class="secret">
              <span>Confirm Password</span>
              <input
                class="input"
                type="password"
                bind:value={confirm}
                placeholder="Confirm your new password"
                autocomplete="off"
                required
              />
            </label>
            {#if passwordProblem}<p class="problem" role="alert">{passwordProblem}</p>{/if}
            {#if passwordNotice}<p class="done" role="status">{passwordNotice}</p>{/if}
            <div class="update"><button type="submit" class="quiet">Update password</button></div>
          </form>
        {/if}
      </section>
    {/if}
  </div>
  <p class="sr-only" role="status">{notice}</p>
  <div class="footer"><button type="button" class="save" onclick={save}>Save</button></div>
</div>

<VariableDialog
  open={editing !== undefined}
  variable={editing?.index === undefined ? undefined : variables[editing.index]}
  taken={variables.filter((_, at) => at !== editing?.index).map((one) => one.key)}
  ondone={doneVariable}
  ondelete={() => {
    variables = variables.filter((_, at) => at !== editing?.index);
    editing = undefined;
  }}
  onclose={() => (editing = undefined)}
/>

<style>
  /* Spacing below as the running app measures it. */
  .picture {
    display: flex;
    align-items: center;
    gap: 16px;
    padding-block-end: 8px;
  }

  .avatar {
    position: relative;
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 40px;
    block-size: 40px;
    overflow: hidden;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-100);
    box-shadow: inset 0 0 0 1px var(--color-gray-200);
    color: var(--color-gray-400);
    transition: box-shadow 200ms;
  }

  .avatar:hover {
    box-shadow: 0 0 0 2px var(--color-gray-300);
  }

  :global([data-theme='dark']) .avatar {
    background-color: rgb(255 255 255 / 0.08);
    box-shadow: inset 0 0 0 1px rgb(255 255 255 / 0.1);
  }

  :global([data-theme='dark']) .avatar:hover {
    box-shadow: 0 0 0 2px rgb(255 255 255 / 0.2);
  }

  .avatar img {
    inline-size: 100%;
    block-size: 100%;
    object-fit: cover;
  }

  .initials {
    color: var(--color-gray-700);
    font-size: var(--text-caption);
  }

  .veil {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    background-color: rgb(0 0 0 / 0.4);
    color: var(--color-white);
    opacity: 0;
    transition: opacity 200ms;
  }

  .avatar:hover .veil {
    opacity: 1;
  }

  .who {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-inline-size: 0;
  }

  .name {
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-gray-400);
  }

  .links {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 11px;
    line-height: calc(20 / 14);
  }

  .links button {
    color: var(--color-gray-500);
    transition: color 100ms;
  }

  .links button:hover {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .links button:hover {
    color: var(--color-gray-300);
  }

  .dot {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .dot {
    color: var(--color-gray-700);
  }

  .field-label {
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    line-height: 20px;
  }

  :global([data-theme='dark']) .field-label {
    color: var(--color-gray-400);
  }

  .field-control {
    margin-block-start: 3px;
  }

  .settings-page .field-note {
    margin-block-start: 2px;
  }

  .input {
    inline-size: 100%;
    block-size: 28px;
    padding-inline: 8px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    transition: border-color 150ms;
  }

  .input::placeholder {
    color: var(--color-gray-300);
  }

  .input:focus {
    border-color: var(--color-blue-400);
    outline: none;
  }

  :global([data-theme='dark']) .input {
    border-color: rgb(255 255 255 / 0.04);
    background-color: rgb(255 255 255 / 0.03);
    color: var(--color-gray-300);
    color-scheme: dark;
  }

  :global([data-theme='dark']) .input::placeholder {
    color: var(--color-gray-700);
  }

  .custom {
    margin-block-start: 4px;
  }

  /* The running app's text area is inline, leaving a line's descender space under it. */
  .bio {
    min-block-size: 60px;
    margin-block-end: 7px;
  }

  .variables-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-block-end: 2px;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  :global([data-theme='dark']) .variables-head {
    color: var(--color-gray-400);
  }

  .count {
    margin-inline-start: 2px;
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .count {
    color: var(--color-gray-600);
  }

  .variable-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-block: 4px;
  }

  .variable {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: var(--text-caption);
  }

  .key {
    min-inline-size: 0;
    overflow: hidden;
    color: var(--color-gray-700);
    font-family: var(--font-mono);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .value {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
    color: var(--color-gray-500);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :global([data-theme='dark']) .key {
    color: var(--color-gray-300);
  }

  .empty {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  :global([data-theme='dark']) .empty {
    color: var(--color-gray-600);
  }

  .settings-page .usage {
    margin-block-start: 0;
  }

  .settings-page .password-note {
    margin-block-start: 2px;
  }

  .password {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding-block: 10px;
  }

  .secret {
    display: flex;
    flex-direction: column;
    gap: 4px;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .secret {
    color: var(--color-gray-400);
  }

  .problem {
    color: var(--color-red-600);
    font-size: var(--text-micro);
  }

  .done {
    color: var(--color-gray-500);
    font-size: var(--text-micro);
  }

  .update {
    display: flex;
    justify-content: flex-end;
  }

  :is(.avatar, .links button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: 2px;
  }
</style>
