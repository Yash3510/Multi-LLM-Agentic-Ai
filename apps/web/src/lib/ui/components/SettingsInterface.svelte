<script lang="ts">
  // Interface settings (chat-composer look §9.4, common look F68): the preference rows, saved with
  // Save. Floating Quick Actions and Image Compression each open a small Manage dialog.
  import { toast } from '$lib/ui/toast.svelte';
  import { untrack } from 'svelte';
  import type { DataSource, UserSettings } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import {
    SECTIONS,
    choiceLabel,
    cycle,
    defaults,
    scaleLabel,
    type PrefRow,
    type PrefValue,
  } from '$lib/ui/interface-prefs';
  import ImageCompressionDialog from './ImageCompressionDialog.svelte';
  import QuickActionsDialog from './QuickActionsDialog.svelte';
  import Switch from './Switch.svelte';
  import './settings-page.css';

  type Props = { source: DataSource; settings: UserSettings };

  let { source, settings }: Props = $props();

  let prefs = $state<Record<string, unknown>>(untrack(() => ({ ...defaults(), ...settings.ui })));
  let notice = $state('');
  let managing = $state<'quickActions' | 'imageCompression'>();
  let backgroundInput = $state<HTMLInputElement>();

  function set(key: string, value: unknown) {
    prefs = { ...prefs, [key]: value };
  }

  // Turning location on asks the browser for it (F68).
  function toggle(row: PrefRow, value: boolean) {
    set(row.key, value);
    if (row.key === 'userLocation' && value) {
      navigator.geolocation?.getCurrentPosition(
        () => (notice = 'User location successfully retrieved.'),
        () => set('userLocation', false),
      );
    }
  }

  function readBackground(file: File | undefined) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => set('chatBackground', reader.result);
    reader.readAsDataURL(file);
  }

  async function save() {
    await source.saveUserSettings({ ui: $state.snapshot(prefs) });
    toast('Settings saved successfully!');
  }
</script>

<div class="settings-page">
  <h2>Interface</h2>
  <p class="lede">How 4CE, the interface and chats look and behave.</p>
  <div class="body">
    <div class="panel">
      {#each SECTIONS as section (section.heading)}
        <h3 class="heading">{section.heading}</h3>
        <div class="rows grouped">
          {#each section.rows as row (row.key)}
            {@const value = prefs[row.key] as PrefValue}
            <div class="block">
              <div class="row">
                <span class="label">{row.label}</span>
                <span class="control">
                  {#if row.kind === 'switch'}
                    <Switch on={value === true} onchange={(next) => toggle(row, next)} />
                  {:else if row.kind === 'cycle'}
                    <button
                      type="button"
                      class="cycle"
                      onclick={() => set(row.key, cycle(row, value))}
                      >{choiceLabel(row, value)}</button
                    >
                  {:else if row.kind === 'scale'}
                    <button
                      type="button"
                      class="cycle"
                      onclick={() => set(row.key, typeof value === 'number' ? undefined : 1)}
                      >{scaleLabel(value)}</button
                    >
                  {:else if row.kind === 'font'}
                    <button
                      type="button"
                      class="cycle"
                      onclick={() => set(row.key, value === undefined ? '' : undefined)}
                      >{value === undefined ? 'Default' : 'Custom'}</button
                    >
                  {:else if row.kind === 'upload'}
                    {#if value}
                      <button type="button" class="cycle" onclick={() => set(row.key, undefined)}
                        >Reset</button
                      >
                    {:else}
                      <button type="button" class="cycle" onclick={() => backgroundInput?.click()}
                        >Upload</button
                      >
                    {/if}
                  {:else if row.kind === 'manage'}
                    {#if value === true}
                      <button
                        type="button"
                        class="cycle"
                        onclick={() => (managing = row.key as typeof managing)}>Manage</button
                      >
                    {/if}
                    <Switch on={value === true} onchange={(next) => set(row.key, next)} />
                  {/if}
                </span>
              </div>
              {#if row.kind === 'scale' && typeof value === 'number'}
                <div class="scale">
                  <button
                    type="button"
                    aria-label="Decrease UI Scale"
                    onclick={() => set(row.key, Math.max(1, Math.round((value - 0.1) * 100) / 100))}
                    ><Icon name="minus" size={14} /></button
                  >
                  <input
                    type="range"
                    min="1"
                    max="1.5"
                    step="0.01"
                    {value}
                    aria-label="UI Scale"
                    oninput={(event) => set(row.key, Number(event.currentTarget.value))}
                  />
                  <button
                    type="button"
                    aria-label="Increase UI Scale"
                    onclick={() =>
                      set(row.key, Math.min(1.5, Math.round((value + 0.1) * 100) / 100))}
                    ><Icon name="plus" size={14} /></button
                  >
                </div>
              {/if}
              {#if row.kind === 'font' && value !== undefined}
                <div class="font">
                  <input
                    value={String(value)}
                    placeholder="Aptos"
                    aria-label="Font Family"
                    oninput={(event) => set(row.key, event.currentTarget.value)}
                  />
                </div>
              {/if}
              <p class="note">{row.note}</p>
            </div>
          {/each}
        </div>
      {/each}
    </div>
  </div>
  <input
    bind:this={backgroundInput}
    type="file"
    accept="image/*"
    hidden
    onchange={(event) => {
      readBackground(event.currentTarget.files?.[0]);
      event.currentTarget.value = '';
    }}
  />
  <p class="sr-only" role="status">{notice}</p>
  <div class="footer"><button type="button" class="save" onclick={save}>Save</button></div>
</div>

<QuickActionsDialog
  open={managing === 'quickActions'}
  actions={prefs.quickActionList as { id: string; label: string; prompt: string }[] | undefined}
  onclose={() => (managing = undefined)}
  onsave={(actions) => {
    set('quickActionList', actions);
    managing = undefined;
  }}
/>
<ImageCompressionDialog
  open={managing === 'imageCompression'}
  size={prefs.imageCompressionSize as { width: string; height: string } | undefined}
  onclose={() => (managing = undefined)}
  onsave={(size) => {
    set('imageCompressionSize', size);
    managing = undefined;
  }}
/>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .heading {
    margin: 0;
    color: var(--color-gray-400);
  }

  .heading:not(:first-child) {
    margin-block-start: 16px;
  }

  :global([data-theme='dark']) .heading {
    color: var(--color-gray-600);
  }

  .label {
    min-inline-size: 0;
  }

  .control {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
  }

  .cycle {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: color 150ms;
  }

  .cycle:hover {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .cycle:hover {
    color: var(--color-white);
  }

  .scale {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 4px 4px;
  }

  .scale button {
    display: grid;
    padding: 4px;
    border-radius: 8px;
    transition: background-color 150ms;
  }

  .scale button:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .scale button:hover {
    background-color: var(--color-gray-800);
  }

  .scale input {
    flex: 1;
  }

  .font {
    margin-block-start: 6px;
    padding-block-end: 4px;
  }

  .font input {
    inline-size: 100%;
    block-size: 28px;
    padding-inline: 8px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-700);
    font-size: var(--text-caption);
  }

  .font input::placeholder {
    color: var(--color-gray-300);
  }

  .font input:focus {
    border-color: var(--color-blue-400);
    outline: none;
  }

  :is(.cycle, .scale button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
