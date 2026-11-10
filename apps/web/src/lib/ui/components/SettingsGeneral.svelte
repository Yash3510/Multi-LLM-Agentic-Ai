<script lang="ts">
  // General settings (chat-composer look §9.3, F92): theme and language apply at once; the system
  // prompt and the advanced parameters save with Save.
  import { untrack } from 'svelte';
  import type { DataSource, UserSettings } from '$lib/data';
  import { getLocale, locales, setLocale } from '$lib/i18n/generated/runtime.js';
  import type { ParamValue } from '$lib/ui/params';
  import { theme, type ThemeChoice } from '$lib/ui/theme.svelte';
  import AdvancedParams from './AdvancedParams.svelte';
  import SettingsSelect from './SettingsSelect.svelte';
  import './settings-page.css';

  type Props = { source: DataSource; settings: UserSettings; admin?: boolean };

  let { source, settings, admin = false }: Props = $props();

  let system = $state(untrack(() => settings.system ?? ''));
  let params = $state<Record<string, ParamValue>>(untrack(() => ({ ...settings.params })));
  let showParams = $state(false);
  let notice = $state('');

  const THEMES = [
    { value: 'system', label: '⚙️ System' },
    { value: 'dark', label: '🌑 Dark' },
    { value: 'oled-dark', label: '🌃 OLED Dark' },
    { value: 'light', label: '☀️ Light' },
  ];
  const LANGUAGES: Record<string, string> = { en: 'English (US)', hi: 'हिन्दी (Hindi)' };

  async function save() {
    await source.saveUserSettings({
      system: system.trim() ? system : undefined,
      params: $state.snapshot(params),
    });
    notice = 'Settings saved successfully!';
  }
</script>

<div class="settings-page">
  <h2>General</h2>
  <div class="body">
    <section>
      <h3>4CE Settings</h3>
      <div class="rows">
        <div>
          <div class="row">
            <span>Theme</span>
            <SettingsSelect
              label="Theme"
              value={theme.choice}
              options={THEMES}
              onchange={(value) => (theme.choice = value as ThemeChoice)}
            />
          </div>
          <p class="note">Choose the color theme used by the interface.</p>
        </div>
        <div>
          <div class="row">
            <span>Language</span>
            <SettingsSelect
              label="Language"
              value={getLocale()}
              options={locales.map((code) => ({ value: code, label: LANGUAGES[code] ?? code }))}
              onchange={(value) => setLocale(value as (typeof locales)[number])}
            />
          </div>
          <p class="note">Choose the language used for interface text.</p>
        </div>
      </div>
    </section>

    <section>
      <h3>System Prompt</h3>
      <textarea
        class="area"
        bind:value={system}
        rows="1"
        placeholder="Enter system prompt here"
        aria-label="System Prompt"></textarea>
      <p class="note field-note">Set the default system prompt for new chats.</p>
    </section>

    <section>
      <h3>Advanced Parameters</h3>
      <div class="row tall">
        <span>Model parameters</span>
        <button type="button" class="quiet" onclick={() => (showParams = !showParams)}
          >{showParams ? 'Hide' : 'Show'}</button
        >
      </div>
      <p class="note">Show or hide custom generation parameters.</p>
      {#if showParams}<div class="params"><AdvancedParams bind:params {admin} /></div>{/if}
    </section>
  </div>
  <p class="sr-only" role="status">{notice}</p>
  <div class="footer"><button type="button" class="save" onclick={save}>Save</button></div>
</div>
