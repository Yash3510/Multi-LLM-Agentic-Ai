<script lang="ts">
  // Keyboard settings (chat-composer look §9.6, F95): shortcuts on or off, and each shortcut's
  // chord. Pressing a chord rebinds at once; a chord another action already uses is refused and
  // named (the running app stored the duplicate). Reset Defaults restores every chord.
  import { untrack } from 'svelte';
  import type { DataSource, UserSettings } from '$lib/data';
  import {
    GROUPS,
    bindings,
    chordFrom,
    conflict,
    formatChord,
    isMac,
    type Chord,
  } from '$lib/ui/shortcuts';
  import Switch from './Switch.svelte';
  import './settings-page.css';

  type Props = { source: DataSource; settings: UserSettings };

  let { source, settings }: Props = $props();

  const mac = isMac();
  let enabled = $state(untrack(() => settings.ui?.shortcutsEnabled !== false));
  let own = $state<Record<string, Chord | null>>(
    untrack(() => ({ ...(settings.ui?.shortcuts as Record<string, Chord | null> | undefined) })),
  );
  let recording = $state<string>();
  let refused = $state<{ id: string; other: string }>();

  const current = $derived(bindings(own));

  async function store(next: Record<string, Chord | null>) {
    own = next;
    await source.saveUserSettings({ ui: { shortcuts: $state.snapshot(next) } });
  }

  // While recording, the next chord rebinds that row; Escape cancels.
  $effect(() => {
    if (!recording) return;
    const id = recording;
    const press = (event: KeyboardEvent) => {
      event.preventDefault();
      if (event.key === 'Escape') {
        recording = undefined;
        return;
      }
      const chord = chordFrom(event, mac);
      if (!chord) return;
      recording = undefined;
      const other = conflict(current, id, chord);
      if (other) {
        refused = { id, other };
        return;
      }
      refused = undefined;
      void store({ ...own, [id]: chord });
    };
    window.addEventListener('keydown', press, true);
    return () => window.removeEventListener('keydown', press, true);
  });
</script>

<div class="settings-page">
  <div class="title-row">
    <h2>Keyboard</h2>
    <button
      type="button"
      class="quiet"
      onclick={() => {
        refused = undefined;
        void store({});
      }}>Reset Defaults</button
    >
  </div>
  <p class="lede">Turn shortcuts on or off, and click a key to rebind it.</p>
  <div class="rows grouped enable">
    <div class="block">
      <div class="row">
        <span>Enable Keyboard Shortcuts</span>
        <Switch
          on={enabled}
          onchange={async (on) => {
            enabled = on;
            await source.saveUserSettings({ ui: { shortcutsEnabled: on } });
          }}
        />
      </div>
      <p class="note">When disabled, keyboard shortcuts will not trigger any actions.</p>
    </div>
  </div>
  <div class="body">
    <div class="table-head"><span class="command">Command</span><span class="key">Key</span></div>
    {#each GROUPS as group (group.name)}
      <div class="group">
        <div class="category">{group.name}</div>
        {#each group.shortcuts as shortcut (shortcut.id)}
          {@const chord = current[shortcut.id]}
          <div class="shortcut">
            <span class="name"
              >{shortcut.label}{#if shortcut.note}<span class="star" title={shortcut.note}>*</span
                >{/if}</span
            >
            <span class="key">
              {#if refused?.id === shortcut.id}
                <span class="conflict" role="alert">Already bound to {refused.other}</span>
              {/if}
              {#if shortcut.fixed}
                <span class="pill">{shortcut.fixed}</span>
              {:else if recording === shortcut.id}
                <span class="pill">Press keys...</span>
              {:else if chord}
                <button
                  type="button"
                  class="pill"
                  title="Click to rebind"
                  onclick={() => (recording = shortcut.id)}>{formatChord(chord, mac)}</button
                >
              {:else}
                <button
                  type="button"
                  class="unassigned"
                  aria-label={`Unassigned: ${shortcut.label.split('\n')[0]}`}
                  onclick={() => (recording = shortcut.id)}>Unassigned</button
                >
              {/if}
            </span>
          </div>
        {/each}
      </div>
    {/each}
  </div>
</div>

<style>
  .title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: 4px;
    /* Clears the dialog's close button. */
    padding-inline-end: 32px;
  }

  .title-row h2 {
    margin: 0;
  }

  .enable {
    margin-block-end: 12px;
  }

  .enable .row {
    gap: 6px;
  }

  .table-head {
    display: flex;
    gap: 8px;
    padding: 0 14px 4px;
    color: var(--color-gray-400);
    font-size: var(--text-nano);
    line-height: calc(20 / 14);
  }

  .command {
    flex: 1;
  }

  .key {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: flex-end;
    gap: 4px;
    inline-size: 152px;
  }

  .group + .group {
    margin-block-start: 12px;
  }

  .category {
    padding: 8px 14px 6px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  :global([data-theme='dark']) :is(.table-head, .category) {
    color: var(--color-gray-600);
  }

  .shortcut {
    display: flex;
    align-items: center;
    gap: 12px;
    min-block-size: 32px;
    padding: 6px 14px;
  }

  /* Every row carries the 1 px rule inside its 32 px, the first one too (under the caption). */
  .shortcut {
    border-block-start: 1px solid color-mix(in srgb, var(--color-gray-100) 70%, transparent);
  }

  :global([data-theme='dark']) .shortcut {
    border-color: rgb(255 255 255 / 0.03);
  }

  .name {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
    color: var(--color-gray-700);
    font-size: 11.5px;
    /* 13 px lines, as the running app measures. */
    line-height: 13px;
    text-overflow: ellipsis;
    white-space: pre-line;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-gray-300);
  }

  .star {
    margin-inline-start: 2px;
    color: var(--color-gray-400);
    font-size: var(--text-nano);
  }

  .pill {
    min-block-size: 18px;
    max-inline-size: 152px;
    padding: 2px 7px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-100);
    color: var(--color-gray-500);
    font-size: var(--text-nano);
    font-weight: var(--font-weight-medium);
    line-height: 1;
    text-align: center;
  }

  :global([data-theme='dark']) .pill {
    background-color: rgb(255 255 255 / 0.06);
    color: var(--color-gray-400);
  }

  .unassigned {
    color: var(--color-gray-500);
    font-size: var(--text-nano);
  }

  .unassigned:hover {
    color: var(--color-gray-400);
  }

  .conflict {
    color: var(--color-amber-500);
    font-size: 9px;
  }

  :is(.pill, .unassigned):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
