<script lang="ts">
  // General settings (F92; ADR-0041 amendment, 2026-11-13): theme and language apply at once; the
  // system prompt and the model parameters wait for Save, which shows only while they differ from
  // what is saved.
  import { toast } from '$lib/ui/toast.svelte';
  import { untrack } from 'svelte';
  import type { DataSource, UserSettings } from '$lib/data';
  import { getLocale, locales, setLocale } from '$lib/i18n/generated/runtime.js';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import type { ParamValue } from '$lib/ui/params';
  import { draftChanged } from '$lib/ui/settings-draft';
  import { theme, type ThemeChoice } from '$lib/ui/theme.svelte';
  import AdvancedParams from './AdvancedParams.svelte';
  import SegmentedControl from './SegmentedControl.svelte';
  import SettingsSelect from './SettingsSelect.svelte';
  import Textarea from './Textarea.svelte';
  import './settings-page.css';

  type Props = { source: DataSource; settings: UserSettings; admin?: boolean };

  let { source, settings, admin = false }: Props = $props();
  const uid = $props.id();

  let saved = $state(
    untrack(() => ({ system: settings.system, params: { ...settings.params } as Params })),
  );
  let system = $state(untrack(() => settings.system ?? ''));
  let params = $state<Params>(untrack(() => ({ ...settings.params })));
  let showParams = $state(false);
  const changed = $derived(draftChanged(saved, system, params));

  type Params = Record<string, ParamValue>;
  const THEMES = [
    { value: 'system', label: 'System', icon: 'monitor' },
    { value: 'light', label: 'Light', icon: 'sun' },
    { value: 'dark', label: 'Dark', icon: 'moon' },
    { value: 'oled-dark', label: 'OLED', icon: 'theme-oled' },
  ] as const;
  const LANGUAGES: Record<string, string> = { en: 'English (US)', hi: 'हिन्दी (Hindi)' };

  async function save() {
    const next = { system: system.trim() ? system : undefined, params: $state.snapshot(params) };
    await source.saveUserSettings(next);
    saved = next;
    toast('Settings saved');
  }

  function reset() {
    system = saved.system ?? '';
    params = { ...saved.params };
  }
</script>

<div class="settings-page">
  <h2>General</h2>
  <div class="body">
    <section>
      <h3>Appearance</h3>
      <div class="group">
        <div class="item">
          <div class="text">
            <span class="name">Theme</span>
            <p class="hint">Choose the color theme used by the interface.</p>
          </div>
          <SegmentedControl
            aria-label="Theme"
            value={theme.choice}
            options={THEMES}
            onValueChange={(value) => (theme.choice = value as ThemeChoice)}
          />
        </div>
      </div>
    </section>

    <section>
      <h3>Language</h3>
      <div class="group">
        <div class="item">
          <div class="text">
            <span class="name">Interface language</span>
            <p class="hint">Choose the language used for interface text.</p>
          </div>
          <SettingsSelect
            label="Language"
            value={getLocale()}
            options={locales.map((code) => ({ value: code, label: LANGUAGES[code] ?? code }))}
            onchange={(value) => setLocale(value as (typeof locales)[number])}
          />
        </div>
      </div>
    </section>

    <section>
      <h3>System prompt</h3>
      <Textarea
        bind:value={system}
        rows={4}
        maxRows={10}
        placeholder="Enter system prompt here"
        aria-label="System prompt"
      />
      <p class="hint under">Set the default system prompt for new chats.</p>
    </section>

    <section>
      <h3>Advanced</h3>
      <div class="group">
        <button
          type="button"
          class="item disclose"
          aria-expanded={showParams}
          aria-labelledby="{uid}-params"
          aria-describedby="{uid}-params-hint"
          onclick={() => (showParams = !showParams)}
        >
          <span class="text">
            <span class="name" id="{uid}-params">Model parameters</span>
            <span class="hint" id="{uid}-params-hint"
              >Show or hide custom generation parameters.</span
            >
          </span>
          <Icon name={showParams ? 'caret-up' : 'sort-caret-down'} size={16} />
        </button>
        {#if showParams}<div class="item open"><AdvancedParams bind:params {admin} /></div>{/if}
      </div>
    </section>
  </div>
  {#if changed}
    <div class="savebar" role="group" aria-label="Unsaved changes">
      <span class="savebar-text" aria-hidden="true">Unsaved changes</span>
      <button type="button" class="quiet" onclick={reset}>Reset</button>
      <button type="button" class="save" onclick={save}>Save</button>
    </div>
  {/if}
</div>
