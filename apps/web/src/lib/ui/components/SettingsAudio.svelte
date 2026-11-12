<script lang="ts">
  // Audio (chat-composer look §9.10, F99): speech-to-text and text-to-speech choices and the voice.
  // The two switches save at once; the rest saves with Save. Only engines and voices that run on
  // this machine are offered: the in-browser model (downloaded from outside) and the browser's
  // network voices (which send the text to the browser vendor) are left out, as the owner chose.
  import { toast } from '$lib/ui/toast.svelte';
  import { untrack } from 'svelte';
  import type { DataSource, UserSettings } from '$lib/data';
  import SettingsSelect from './SettingsSelect.svelte';
  import Switch from './Switch.svelte';
  import './settings-page.css';

  type Props = { source: DataSource; settings: UserSettings };

  let { source, settings }: Props = $props();

  type Audio = { sttLanguage?: string; playbackRate?: number; voice?: string };
  const saved = untrack(() => (settings.ui?.audio ?? {}) as Audio);
  const ui = untrack(() => settings.ui ?? {});

  let language = $state(saved.sttLanguage ?? '');
  let rate = $state(saved.playbackRate ?? 1);
  let voice = $state(saved.voice ?? '');
  let autoSend = $state(ui.speechAutoSend === true);
  let autoPlay = $state(ui.responseAutoPlayback === true);
  let voices = $state<string[]>([]);
  let notice = $state('');

  const DEFAULT = [{ value: '', label: 'Default' }];

  // The browser fills its voice list a moment after the page loads.
  $effect(() => {
    const speech = globalThis.speechSynthesis;
    if (!speech) return;
    const read = () =>
      (voices = speech
        .getVoices()
        .filter((one) => one.localService)
        .map((one) => one.name));
    read();
    speech.addEventListener('voiceschanged', read);
    return () => speech.removeEventListener('voiceschanged', read);
  });

  async function setAutoSend(on: boolean) {
    autoSend = on;
    await source.saveUserSettings({ ui: { speechAutoSend: on } });
  }

  async function setAutoPlay(on: boolean) {
    autoPlay = on;
    await source.saveUserSettings({ ui: { responseAutoPlayback: on } });
  }

  async function save() {
    const audio: Audio = {
      sttLanguage: language.trim() || undefined,
      playbackRate: rate,
      voice: voice || undefined,
    };
    await source.saveUserSettings({ ui: { audio } });
    toast('Settings saved successfully!');
  }
</script>

<div class="settings-page">
  <h2>Audio</h2>
  <div class="body">
    <section>
      <h3>STT Settings</h3>
      <div class="rows grouped">
        <div class="block">
          <div class="row">
            <span>Speech-to-Text Engine</span>
            <SettingsSelect
              label="Speech-to-Text Engine"
              value=""
              options={DEFAULT}
              onchange={() => {}}
            />
          </div>
          <p class="note">Choose the engine used to transcribe voice input.</p>
        </div>
        <div class="block">
          <div class="row">
            <span>Language</span>
            <input
              class="field language"
              bind:value={language}
              aria-label="Speech-to-Text Language"
              placeholder="e.g. en"
              title="The language of the input audio, as an ISO-639-1 code (e.g. en). Supplying it improves accuracy and speed; leave it blank to detect it automatically."
            />
          </div>
          <p class="note">
            Set a speech recognition language or leave it blank to detect automatically.
          </p>
        </div>
        <div class="block">
          <div class="row">
            <span>Instant Auto-Send After Voice Transcription</span>
            <Switch on={autoSend} onchange={setAutoSend} />
          </div>
          <p class="note">
            Send transcribed voice input immediately after speech recognition finishes.
          </p>
        </div>
      </div>
    </section>
    <section>
      <h3>TTS Settings</h3>
      <div class="rows grouped">
        <div class="block">
          <div class="row">
            <span>Text-to-Speech Engine</span>
            <SettingsSelect
              label="Text-to-Speech Engine"
              value=""
              options={DEFAULT}
              onchange={() => {}}
            />
          </div>
          <p class="note">Choose the engine used to read assistant responses aloud.</p>
        </div>
        <div class="block">
          <div class="row">
            <span>Auto-Playback Response</span>
            <Switch on={autoPlay} onchange={setAutoPlay} />
          </div>
          <p class="note">Play assistant responses aloud automatically.</p>
        </div>
        <div class="block">
          <div class="row">
            <span>Speech Playback Speed</span>
            <span class="speed">
              <input
                class="field rate"
                type="number"
                min="0"
                step="0.01"
                bind:value={rate}
                aria-label="Speech Playback Speed"
              />
              <span class="suffix">x</span>
            </span>
          </div>
          <p class="note">Adjust how quickly spoken responses are played.</p>
        </div>
      </div>
    </section>
    <section>
      <h3>Voice</h3>
      <div class="voice">
        <span class="row">Set Voice</span>
        <SettingsSelect
          label="Voice"
          value={voice}
          options={[...DEFAULT, ...voices.map((name) => ({ value: name, label: name }))]}
          onchange={(value) => (voice = value)}
          wide
        />
        <p class="note">Choose the browser voice used for speech output.</p>
      </div>
    </section>
  </div>
  <p class="sr-only" role="status">{notice}</p>
  <div class="footer"><button type="button" class="save" onclick={save}>Save</button></div>
</div>

<style>
  .field {
    block-size: 28px;
    padding-inline: 8px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    text-align: end;
    transition: border-color 150ms;
  }

  .field::placeholder {
    color: var(--color-gray-300);
  }

  .field:focus {
    border-color: var(--color-blue-400);
    outline: none;
  }

  :global([data-theme='dark']) .field {
    border-color: rgb(255 255 255 / 0.04);
    background-color: rgb(255 255 255 / 0.03);
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .field::placeholder {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .field:focus {
    border-color: var(--color-blue-500);
  }

  .language {
    inline-size: 96px;
  }

  .rate {
    inline-size: 64px;
    appearance: textfield;
  }

  .rate::-webkit-inner-spin-button {
    appearance: none;
  }

  .speed {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .suffix {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .suffix {
    color: var(--color-gray-600);
  }

  /* As the running app measures: the label 3 px lower than a row, the select 6 px under it and
     the note 2 px under the select. */
  .voice {
    display: flex;
    flex-direction: column;
    padding-block-start: 3px;
  }

  .voice > .row {
    margin-block-end: 6px;
  }

  .voice .note {
    margin-block-start: 2px;
  }
</style>
