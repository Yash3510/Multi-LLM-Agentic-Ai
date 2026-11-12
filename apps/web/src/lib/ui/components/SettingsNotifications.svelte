<script lang="ts">
  // Notification settings (chat-composer look §9.5, F94): browser notifications (asks the
  // browser first) and the notification sound, each saved at once. Notification targets
  // (outgoing webhooks) are not offered: they send chat status off the machine.
  import { untrack } from 'svelte';
  import type { DataSource, UserSettings } from '$lib/data';
  import Switch from './Switch.svelte';
  import './settings-page.css';

  type Props = { source: DataSource; settings: UserSettings };

  let { source, settings }: Props = $props();

  let browser = $state(untrack(() => settings.ui?.browserNotifications === true));
  let sound = $state(untrack(() => settings.ui?.notificationSound !== false));
  let problem = $state('');

  async function setBrowser(on: boolean) {
    problem = '';
    if (on && globalThis.Notification) {
      const answer = await Notification.requestPermission();
      if (answer !== 'granted') {
        problem =
          'Your browser blocks notifications for this site; allow them in its settings first.';
        return;
      }
    }
    browser = on;
    await source.saveUserSettings({ ui: { browserNotifications: on } });
  }

  async function setSound(on: boolean) {
    sound = on;
    await source.saveUserSettings({ ui: { notificationSound: on } });
  }
</script>

<div class="settings-page">
  <h2>Notifications</h2>
  <div class="body">
    <div class="rows grouped">
      <div class="block">
        <div class="row">
          <span>Browser Notifications</span>
          <Switch on={browser} onchange={setBrowser} />
        </div>
        <p class="note">Allow browser notifications for completed responses.</p>
        {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
      </div>
      <div class="block">
        <div class="row">
          <span>Notification Sound</span>
          <Switch on={sound} onchange={setSound} />
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .problem {
    margin-block-start: 4px;
    color: var(--color-red-600);
    font-size: var(--text-micro);
  }
</style>
