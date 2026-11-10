<script lang="ts">
  // The settings dialog (chat-composer look §9.1, F91): Back, search, the person's tabs under
  // their captions, and the chosen page. The admin tabs join with the admin area; Connections is
  // left out, as the owner chose.
  import { Dialog } from 'bits-ui';
  import type { DataSource, UserSettings } from '$lib/data';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { ADMIN_GROUPS, PANELS, type PanelId } from '$lib/ui/admin-panels';
  import AdminAnalytics from './AdminAnalytics.svelte';
  import AdminConnections from './AdminConnections.svelte';
  import AdminModels from './AdminModels.svelte';
  import AdminSettings from './AdminSettings.svelte';
  import SettingsAccount from './SettingsAccount.svelte';
  import SettingsArchived from './SettingsArchived.svelte';
  import SettingsAudio from './SettingsAudio.svelte';
  import SettingsData from './SettingsData.svelte';
  import SettingsGeneral from './SettingsGeneral.svelte';
  import SettingsInterface from './SettingsInterface.svelte';
  import SettingsKeyboard from './SettingsKeyboard.svelte';
  import SettingsNotifications from './SettingsNotifications.svelte';
  import SettingsPersonalization from './SettingsPersonalization.svelte';
  import SettingsUsage from './SettingsUsage.svelte';
  import './modal.css';

  type Props = {
    open: boolean;
    source: DataSource;
    admin?: boolean;
    onclose: () => void;
  };

  let { open, source, admin = false, onclose }: Props = $props();

  type Tab = { id: string; label: string; icon: IconName };
  const GROUPS: { caption: string; tabs: Tab[] }[] = [
    {
      caption: 'Basics',
      tabs: [
        { id: 'general', label: 'General', icon: 'settings-general' },
        { id: 'interface', label: 'Interface', icon: 'settings-interface' },
        { id: 'notifications', label: 'Notifications', icon: 'settings-notifications' },
        { id: 'keyboard', label: 'Keyboard', icon: 'settings-keyboard' },
      ],
    },
    {
      caption: 'Preferences',
      tabs: [
        { id: 'personalization', label: 'Personalization', icon: 'settings-personalization' },
        { id: 'audio', label: 'Audio', icon: 'settings-audio' },
      ],
    },
    {
      caption: 'Data',
      tabs: [
        { id: 'data', label: 'Data Controls', icon: 'settings-data' },
        { id: 'usage', label: 'Usage', icon: 'settings-usage' },
        { id: 'archived', label: 'Archived Chats', icon: 'settings-archived' },
      ],
    },
    { caption: 'Profile', tabs: [{ id: 'account', label: 'Account', icon: 'settings-account' }] },
  ];

  let tab = $state('general');
  let query = $state('');
  let settings = $state<UserSettings>();

  const matching = (groups: typeof GROUPS) =>
    groups
      .map((group) => ({
        ...group,
        tabs: group.tabs.filter((one) =>
          one.label.toLowerCase().includes(query.trim().toLowerCase()),
        ),
      }))
      .filter((group) => group.tabs.length);
  const shown = $derived(matching(GROUPS));
  // Admins see the admin tabs under their own captions (admin look §18).
  const shownAdmin = $derived(admin ? matching(ADMIN_GROUPS) : []);
  const current = $derived(
    [...GROUPS, ...ADMIN_GROUPS].flatMap((group) => group.tabs).find((one) => one.id === tab),
  );
  /** The schema panel behind an admin tab, when it is built that way. */
  const adminPanel = $derived.by(() => {
    const id = tab.replace(/^admin-/, '');
    return tab.startsWith('admin-') && id in PANELS ? (id as PanelId) : undefined;
  });

  // Each opening starts on General with fresh settings.
  $effect(() => {
    if (!open) return;
    tab = 'general';
    query = '';
    void source.getUserSettings().then((loaded) => (settings = loaded));
  });
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame settings-frame" aria-describedby={undefined}>
      <Dialog.Title class="sr-only">Settings</Dialog.Title>
      <div class="card">
        <nav aria-label="Settings">
          <button type="button" class="back" onclick={onclose}>
            <Icon name="caret-left" size={12} /><span>Back</span>
          </button>
          <label class="search">
            <Icon name="magnifying-glass" size={14} />
            <span class="sr-only">Search</span>
            <input bind:value={query} placeholder="Search" />
          </label>
          <div class="tabs">
            {#if shown.length}
              <span class="caption first">Personal</span>
              {#each shown as group, index (group.caption)}
                <span class="caption" class:lead={index === 0}>{group.caption}</span>
                {#each group.tabs as one (one.id)}
                  <button
                    type="button"
                    class="tab"
                    aria-current={one.id === tab ? 'page' : undefined}
                    onclick={() => (tab = one.id)}
                  >
                    <Icon name={one.icon} size={14} /><span>{one.label}</span>
                  </button>
                {/each}
              {/each}
            {/if}
            {#if shownAdmin.length}
              <div class="admin-rule"></div>
              <span class="caption admin-caption">Admin</span>
              {#each shownAdmin as group, index (group.caption)}
                <span class="caption" class:lead={index === 0}>{group.caption}</span>
                {#each group.tabs as one (one.id)}
                  <button
                    type="button"
                    class="tab"
                    aria-current={one.id === tab ? 'page' : undefined}
                    onclick={() => (tab = one.id)}
                  >
                    <Icon name={one.icon} size={14} /><span>{one.label}</span>
                  </button>
                {/each}
              {/each}
            {/if}
            {#if !shown.length && !shownAdmin.length}
              <p class="none">No matches</p>
            {/if}
          </div>
        </nav>
        <div class="content">
          {#if settings && tab === 'general'}
            <SettingsGeneral {source} {settings} {admin} />
          {:else if settings && tab === 'interface'}
            <SettingsInterface {source} {settings} />
          {:else if settings && tab === 'notifications'}
            <SettingsNotifications {source} {settings} />
          {:else if settings && tab === 'keyboard'}
            <SettingsKeyboard {source} {settings} />
          {:else if settings && tab === 'personalization'}
            <SettingsPersonalization {source} {settings} />
          {:else if settings && tab === 'audio'}
            <SettingsAudio {source} {settings} />
          {:else if tab === 'data'}
            <SettingsData {source} />
          {:else if tab === 'usage'}
            <SettingsUsage {source} />
          {:else if tab === 'archived'}
            <SettingsArchived {source} />
          {:else if tab === 'account'}
            <SettingsAccount {source} />
          {:else if admin && tab === 'admin-models'}
            <AdminModels {source} />
          {:else if admin && tab === 'admin-analytics'}
            <AdminAnalytics {source} />
          {:else if admin && tab === 'admin-connections'}
            <AdminConnections {source} />
          {:else if adminPanel}
            <AdminSettings {source} panel={adminPanel} />
          {:else if current}
            <!-- The other pages land one at a time. -->
            <h2 class="page-title">{current.label}</h2>
          {/if}
        </div>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  /* 16 px round the panel, 24 from 640 px, 32 from 1024 px (look §9.1). */
  :global(.settings-frame) {
    padding: 16px calc(16px + 0.45rem) 16px 16px;
  }

  @media (min-width: 40rem) {
    :global(.settings-frame) {
      padding: 24px calc(24px + 0.45rem) 24px 24px;
    }
  }

  @media (min-width: 64rem) {
    :global(.settings-frame) {
      padding: 32px calc(32px + 0.45rem) 32px 32px;
    }
  }

  .card {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    max-inline-size: 1280px;
    block-size: min(max(864px, 80dvh), calc(100dvh - 64px));
    margin: auto;
    overflow: hidden;
    border: 1px solid var(--color-white);
    border-radius: 32px;
    background-color: var(--color-white);
  }

  @media (min-width: 48rem) {
    .card {
      flex-direction: row;
    }
  }

  :global([data-theme='dark']) .card {
    border-color: var(--color-gray-850);
    background-color: var(--color-gray-900);
    color: var(--color-gray-100);
  }

  nav {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    border-block-end: 1px solid color-mix(in srgb, var(--color-gray-100) 30%, transparent);
  }

  @media (min-width: 48rem) {
    nav {
      inline-size: 240px;
      border-block-end: 0;
      border-inline-end: 1px solid color-mix(in srgb, var(--color-gray-100) 30%, transparent);
    }
  }

  :global([data-theme='dark']) nav {
    border-color: rgb(255 255 255 / 0.02);
  }

  .back,
  .tab {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    block-size: 28px;
    padding-inline: 8px;
    border-radius: 8px;
    font-size: var(--text-caption);
    line-height: 16px;
    text-align: start;
    transition: color 75ms;
  }

  .back {
    margin: 4px;
    color: var(--color-gray-400);
  }

  @media (min-width: 48rem) {
    .back {
      margin-block-end: 0;
    }
  }

  .back:hover {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .back {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .back:hover {
    color: var(--color-gray-300);
  }

  .search {
    display: none;
    align-items: center;
    gap: 6px;
    block-size: 28px;
    margin: 4px 4px 2px;
    padding-inline: 8px;
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 70%, transparent);
    font-size: var(--text-caption);
  }

  @media (min-width: 48rem) {
    .search {
      display: flex;
    }
  }

  :global([data-theme='dark']) .search {
    background-color: rgb(255 255 255 / 0.03);
  }

  .search input {
    flex: 1;
    min-inline-size: 0;
    padding-block: 4px;
    line-height: 16px;
    background: transparent;
    color: inherit;
    font-size: var(--text-caption);
  }

  .search input:focus {
    outline: none;
  }

  .search input::placeholder {
    color: var(--color-gray-400);
  }

  .tabs {
    display: flex;
    gap: 1px;
    padding: 4px 4px 4px 0;
    overflow-x: auto;
    scrollbar-width: none;
  }

  @media (min-width: 48rem) {
    .tabs {
      flex-direction: column;
      padding: 4px;
      overflow-x: visible;
      overflow-y: auto;
    }

    .tab {
      inline-size: 100%;
    }
  }

  .caption {
    display: none;
    margin-block: 8px 2px;
    padding-inline: 8px;
    color: var(--color-gray-400);
    font-size: var(--text-nano);
    line-height: 15px;
  }

  /* As the running app measures: "Personal" 6 px down, its first group 2 px under it. */
  .caption.first {
    margin-block-start: 6px;
  }

  /* The admin block (admin look §18): a rule, then "Admin" 2 px above its first group. */
  .admin-rule {
    display: none;
    block-size: 1px;
    margin: 8px 4px;
    background-color: color-mix(in srgb, var(--color-gray-100) 40%, transparent);
  }

  :global([data-theme='dark']) .admin-rule {
    background-color: rgb(255 255 255 / 0.025);
  }

  @media (min-width: 48rem) {
    .admin-rule {
      display: block;
    }
  }

  .caption.admin-caption {
    margin-block-start: 0;
  }

  .caption.lead {
    margin-block-start: 2px;
  }

  @media (min-width: 48rem) {
    .caption {
      display: block;
    }
  }

  :global([data-theme='dark']) .caption {
    color: var(--color-gray-600);
  }

  .tab {
    color: var(--color-gray-500);
  }

  .tab:hover {
    color: var(--color-gray-700);
  }

  .tab[aria-current] {
    background-color: var(--color-gray-50);
    color: var(--color-gray-900);
    font-weight: var(--font-weight-medium);
  }

  :global([data-theme='dark']) .tab:hover {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) .tab[aria-current] {
    background-color: rgb(255 255 255 / 0.04);
    color: var(--color-white);
  }

  .none {
    padding: 4px 8px;
    color: var(--color-gray-400);
    font-size: var(--text-caption);
  }

  .content {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
    min-inline-size: 0;
    padding: 16px;
    overflow: hidden;
  }

  @media (min-width: 48rem) {
    .content {
      padding-inline: 20px;
    }
  }

  .page-title {
    color: var(--color-gray-900);
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
    line-height: 20px;
  }

  :global([data-theme='dark']) .page-title {
    color: var(--color-white);
  }

  :is(.back, .tab):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
