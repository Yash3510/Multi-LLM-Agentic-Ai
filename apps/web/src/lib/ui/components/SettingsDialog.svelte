<script lang="ts">
  // The settings dialog (F91; ADR-0041 amendment, 2026-11-13): a title, the Personal or Admin
  // switch for admins, search, that side's tabs under their captions, and the chosen page. The
  // person's Connections tab is left out, as the owner chose.
  import { Dialog } from 'bits-ui';
  import type { DataSource, UserSettings } from '$lib/data';
  import { ICONS, type IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { ADMIN_GROUPS, PANELS, type PanelId } from '$lib/ui/admin-panels';
  import { glide } from '$lib/ui/glide';
  import { scopeOf, shownGroups, type Scope } from '$lib/ui/settings-nav';
  import AdminAnalytics from './AdminAnalytics.svelte';
  import AdminConnections from './AdminConnections.svelte';
  import AdminModels from './AdminModels.svelte';
  import AdminSettings from './AdminSettings.svelte';
  import SegmentedControl from './SegmentedControl.svelte';
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
  import './glide.css';
  import './modal.css';

  type Props = {
    open: boolean;
    source: DataSource;
    admin?: boolean;
    onclose: () => void;
  };

  let { open, source, admin = false, onclose }: Props = $props();

  type Tab = { id: string; label: string; icon: IconName };
  const SIDES = [
    { value: 'personal', label: 'Personal' },
    { value: 'admin', label: 'Admin' },
  ];
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

  let scope = $state<Scope>('personal');

  const shown = $derived(shownGroups<Tab>(GROUPS, ADMIN_GROUPS, scope, query, admin));
  /** The selected tab's icon is the filled twin of its own, where the registry has one. */
  const filled = (icon: IconName): IconName => {
    const twin = `${icon}-fill`;
    return twin in ICONS ? (twin as IconName) : icon;
  };

  // Changing side opens that side's first page, so the list always holds the open tab.
  function side(next: string) {
    scope = next as Scope;
    if (scopeOf(tab) !== scope) tab = scope === 'admin' ? ADMIN_GROUPS[0].tabs[0].id : 'general';
  }

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
    scope = 'personal';
    query = '';
    void source.getUserSettings().then((loaded) => (settings = loaded));
  });

  // On narrow screens the tab row scrolls so the open tab starts it.
  const reveal = (active: boolean) => (node: HTMLElement) => {
    if (active && node.parentElement)
      node.parentElement.scrollLeft = node.offsetLeft - node.parentElement.offsetLeft;
  };
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop settings-backdrop" />
    <Dialog.Content class="modal-frame settings-frame" aria-describedby={undefined}>
      <div class="card">
        <button type="button" class="close" aria-label="Close" onclick={onclose}>
          <Icon name="x" size={16} />
        </button>
        <nav aria-label="Settings">
          <Dialog.Title class="settings-title">Settings</Dialog.Title>
          {#if admin}
            <div class="sides">
              <SegmentedControl
                fill
                aria-label="Whose settings"
                value={scope}
                options={SIDES}
                onValueChange={side}
              />
            </div>
          {/if}
          <label class="search">
            <Icon name="magnifying-glass" size={14} />
            <span class="sr-only">Search</span>
            <input bind:value={query} placeholder="Search" />
          </label>
          <div class="tabs" {@attach glide({ active: '.tab[aria-current]', hover: '.tab' })}>
            {#each shown as group (group.tabs[0].id)}
              <span class="caption">{group.caption}</span>
              {#each group.tabs as one (one.id)}
                <button
                  type="button"
                  class="tab"
                  aria-current={one.id === tab ? 'page' : undefined}
                  {@attach reveal(one.id === tab)}
                  onclick={() => ((tab = one.id), (scope = scopeOf(one.id)))}
                >
                  <Icon name={one.id === tab ? filled(one.icon) : one.icon} size={16} /><span
                    >{one.label}</span
                  >
                </button>
              {/each}
            {:else}
              <p class="none">No matches</p>
            {/each}
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
  /* A softer dim than the working dialogs: settings is a place to look round, not a question. */
  :global(.settings-backdrop) {
    background-color: rgb(0 0 0 / 0.3);
  }

  :global([data-theme='dark'] .settings-backdrop) {
    background-color: rgb(0 0 0 / 0.5);
  }

  :global(.settings-frame) {
    padding: 16px calc(16px + 0.45rem) 16px 16px;
  }

  @media (min-width: 40rem) {
    :global(.settings-frame) {
      padding: 24px calc(24px + 0.45rem) 24px 24px;
    }
  }

  /* 920 by 640 at most (ADR-0041 amendment, 2026-11-13): a label and its control stay one row. */
  .card {
    position: relative;
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    max-inline-size: 920px;
    block-size: min(640px, calc(100dvh - 48px));
    margin: auto;
    overflow: hidden;
    border: 1px solid var(--color-line-1);
    /* Rounder than a panel, and its switches and selects are pills (ADR-0041, 2026-11-13). */
    --segmented-radius: var(--radius-pill);
    --segmented-inner-radius: var(--radius-pill);
    border-radius: 32px;
    background-color: var(--color-surface-raised);
    box-shadow: var(--shadow-e3), var(--glass-edge);
    color: var(--color-ink-1);
  }

  @media (min-width: 48rem) {
    .card {
      flex-direction: row;
    }
  }

  :global([data-theme='dark']) .card {
    background-color: var(--color-gray-900);
  }

  .close {
    position: absolute;
    inset-block-start: 12px;
    inset-inline-end: 12px;
    z-index: 1;
    display: grid;
    place-items: center;
    inline-size: 28px;
    block-size: 28px;
    border-radius: var(--radius-pill);
    color: var(--color-ink-3);
  }

  .close:hover {
    background-color: var(--color-tint);
    color: var(--color-ink-1);
  }

  /* On a narrow screen: the title, then the switch, then the tabs as one scrolling row. */
  nav {
    display: flex;
    flex-shrink: 0;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    padding: 14px 12px 8px;
    border-block-end: 1px solid var(--color-line-1);
  }

  @media (min-width: 48rem) {
    nav {
      flex-direction: column;
      flex-wrap: nowrap;
      align-items: stretch;
      gap: 0;
      inline-size: 224px;
      padding: 16px 10px 0;
      border-block-end: 0;
      border-inline-end: 1px solid var(--color-line-1);
      background-color: var(--glass-soft);
    }
  }

  :global(.settings-title) {
    flex: 1 1 100%;
    padding-inline: 8px 40px;
    color: var(--color-ink-1);
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
    line-height: 20px;
  }

  /* Never squeezed: both sides stay readable beside the search on a narrow screen. */
  .sides {
    flex: none;
    inline-size: 200px;
  }

  @media (min-width: 48rem) {
    :global(.settings-title) {
      flex: none;
      padding-block-end: 12px;
      padding-inline-end: 8px;
    }

    .sides {
      inline-size: auto;
      margin-block-end: 10px;
    }
  }

  .tab {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 8px;
    block-size: 30px;
    padding-inline: 10px;
    border-radius: var(--radius-pill);
    color: var(--color-ink-2);
    font-size: var(--text-caption);
    line-height: 16px;
    text-align: start;
  }

  .search {
    display: none;
    align-items: center;
    gap: 6px;
    block-size: 30px;
    margin-block-end: 6px;
    padding-inline: 12px;
    border-radius: var(--radius-pill);
    background-color: transparent;
    background-image: var(--field-inset-fill);
    box-shadow: var(--field-inset-edge);
    color: var(--color-ink-3);
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
    color: var(--color-ink-1);
    font-size: var(--text-caption);
  }

  .search input:focus {
    outline: none;
  }

  .search input::placeholder {
    color: var(--color-ink-3);
  }

  .tabs {
    display: flex;
    flex: 1 1 100%;
    min-inline-size: 0;
    gap: 1px;
    overflow-x: auto;
    scrollbar-width: none;
  }

  /* The list fades out at the foot where it scrolls; the padding keeps the last tab clear of it. */
  @media (min-width: 48rem) {
    .tabs {
      flex: 1;
      flex-direction: column;
      min-block-size: 0;
      padding-block-end: 20px;
      overflow-x: visible;
      overflow-y: auto;
      mask-image: linear-gradient(to bottom, black calc(100% - 20px), transparent);
    }

    .tab {
      inline-size: 100%;
    }
  }

  .caption {
    display: none;
    margin-block: 12px 4px;
    padding-inline: 10px;
    color: var(--color-ink-3);
    font-size: var(--text-nano);
    line-height: 15px;
  }

  .caption:first-of-type {
    margin-block-start: 4px;
  }

  @media (min-width: 48rem) {
    .caption {
      display: block;
    }
  }

  .tab:hover {
    color: var(--color-ink-1);
  }

  .tab[aria-current] {
    background-color: var(--color-tint);
    color: var(--color-ink-1);
    font-weight: var(--font-weight-medium);
  }

  /* With the sliding highlight attached, the marker paints the fill the open tab used to. */
  .tabs {
    --glide-fill: var(--color-tint);
    --glide-hover-fill: color-mix(in srgb, var(--color-tint) 55%, transparent);
  }

  @media (forced-colors: none) {
    .tabs:global([data-glide-host]) .tab[aria-current] {
      background-color: transparent;
    }
  }

  .none {
    padding: 4px 10px;
    color: var(--color-ink-3);
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
      padding: 18px 24px 16px;
    }
  }

  .page-title {
    color: var(--color-ink-1);
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
    line-height: 20px;
  }

  :is(.close, .tab):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
