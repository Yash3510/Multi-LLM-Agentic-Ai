<script lang="ts">
  // The signed-in frame (layout look §2.1, §3): the sidebar beside the main area, full viewport
  // height. Chats come from the data source; pinned destinations point at planned routes.
  import { page } from '$app/state';
  import { m } from '$lib/i18n/generated/messages.js';
  import GroupHeading from './GroupHeading.svelte';
  import ListRow from './ListRow.svelte';
  import NodeGlyph from './NodeGlyph.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Sidebar, { type Destination } from './Sidebar.svelte';
  import { formatAgo, timeGroup, toIntlLocale } from '$lib/ui/format';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import type { Snippet } from 'svelte';
  import { goto, invalidateAll } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { data as source, type ChatSummary, type User } from '$lib/data';
  import SettingsDialog from './SettingsDialog.svelte';
  import StatusDialog from './StatusDialog.svelte';
  import UserMenu from './UserMenu.svelte';
  import { provideOpenSettings } from '$lib/ui/settings-context';

  let {
    children,
    chats,
    userName,
    user,
  }: { children: Snippet; chats: ChatSummary[]; userName: string; user?: User } = $props();

  // The user menu hangs from the avatar that was pressed (layout look §7.1).
  let menuOpen = $state(false);
  let menuAnchor = $state<HTMLElement>();
  let settingsOpen = $state(false);
  let statusOpen = $state(false);
  let active = $state(1);
  provideOpenSettings(() => (settingsOpen = true));

  const locale = toIntlLocale(getLocale());
  // Planned routes (web-screens.md); the hash keeps them typed until they exist.
  // Channels join the pinned destinations when the admin switches them on (admin General).
  let features = $state<Record<string, unknown>>({});
  void source.getAdminSettings('general').then((values) => (features = values));
  const channelsOn = $derived(features.ENABLE_CHANNELS === true);
  const DESTINATIONS: Destination[] = $derived([
    { href: '/notes', label: 'Notes', icon: 'note' },
    ...(channelsOn
      ? [{ href: '/channels', label: 'Channels', icon: 'chats-circle' } as Destination]
      : []),
    ...(features.ENABLE_CALENDAR === true
      ? [{ href: '/calendar', label: 'Calendar', icon: 'clock' } as Destination]
      : []),
    ...(features.ENABLE_AUTOMATIONS === true
      ? [{ href: '/automations', label: 'Automations', icon: 'lightning' } as Destination]
      : []),
    { href: '/workspace', label: 'Workspace', icon: 'workspace' },
  ]);

  const rows = $derived(
    chats.map((chat, index) => {
      const group = timeGroup(chat.updated);
      const before = index > 0 ? timeGroup(chats[index - 1].updated) : undefined;
      return {
        ...chat,
        heading: JSON.stringify(group) === JSON.stringify(before) ? undefined : group,
      };
    }),
  );

  // Closed until the person opens it, as a fresh browser shows the running app; the choice is
  // remembered (a convenience only, so a blocked store just means closed).
  const SIDEBAR_KEY = '4ce.sidebar';
  const stored = () => {
    try {
      return localStorage.getItem(SIDEBAR_KEY) === 'open';
    } catch {
      return false;
    }
  };
  let open = $state(stored());
  $effect(() => {
    try {
      localStorage.setItem(SIDEBAR_KEY, open ? 'open' : 'closed');
    } catch {
      // Storage blocked: the sidebar simply starts closed next time.
    }
  });

  // The run marker's screen-reader text (layout look §4.4).
  const OUTCOME = {
    released: 'Released',
    withheld: 'Withheld',
    interrupted: 'Stopped',
    done: 'Done',
  } as const;
</script>

<div class="frame">
  <Sidebar
    bind:open
    productName={m.app_name()}
    {userName}
    destinations={DESTINATIONS}
    current={page.url.pathname + page.url.hash}
    onusermenu={async (event) => {
      menuAnchor = event.currentTarget as HTMLElement;
      active = await source.activeUsers();
      menuOpen = true;
    }}
  >
    <div class="section">
      <span class="section-label">Folders</span>
      <button type="button" class="section-action" aria-label="New Folder" title="New Folder">
        <Icon name="plus" size={14} />
      </button>
    </div>
    <div class="section">
      <span class="section-label">Chats</span>
      <button type="button" class="section-action" aria-label="More" title="More">
        <Icon name="row-more" size={14} />
      </button>
    </div>
    <div class="chats">
      {#each rows as row, index (row.id)}
        {#if row.heading}
          <GroupHeading group={row.heading} first={index === 0} variant="sidebar" />
        {/if}
        <div class="row-wrap">
          <ListRow
            href={`/c/${row.id}`}
            variant="sidebar"
            current={page.url.pathname === `/c/${row.id}`}
          >
            <span class="marker">
              {#if row.outcome === 'direct'}
                <span class="direct" role="img" aria-label="Direct reply"></span>
              {:else if row.outcome}
                <NodeGlyph state={row.outcome} label={OUTCOME[row.outcome]} />
              {/if}
            </span>
            <span class="title truncate">{row.title}</span>
            {#if page.url.pathname !== `/c/${row.id}`}
              <time class="ago" datetime={row.updated.toISOString()}>
                {formatAgo(row.updated, { locale })}
              </time>
            {/if}
          </ListRow>
          <!-- The menu button takes the time's place on the open chat (layout look §4.4), and on
               any row under the pointer or holding focus, as on the running app. -->
          <button
            type="button"
            class="row-more"
            data-current={page.url.pathname === `/c/${row.id}` ? '' : undefined}
            aria-label="Chat Menu"
            title="More"
          >
            <Icon name="row-more" size={14} />
          </button>
        </div>
      {/each}
    </div>
  </Sidebar>
  <main id="main" class="main">
    {@render children()}
  </main>
</div>

{#if user}
  <UserMenu
    bind:open={menuOpen}
    {user}
    {active}
    anchor={menuAnchor}
    onsettings={() => (settingsOpen = true)}
    onstatus={() => (statusOpen = true)}
    onsignout={async () => {
      await source.signOut();
      await goto(resolve('/auth'), { invalidateAll: true });
    }}
  />
  <SettingsDialog
    open={settingsOpen}
    {source}
    admin={user.role === 'admin'}
    onclose={() => (settingsOpen = false)}
  />
  <StatusDialog
    open={statusOpen}
    message={user.status?.message}
    onclose={() => (statusOpen = false)}
    onsave={async (message) => {
      await source.setStatus(message ? { message } : undefined);
      statusOpen = false;
      await invalidateAll();
    }}
  />
{/if}

<style>
  .frame {
    display: flex;
    block-size: 100dvh;
    overflow: hidden;
    background-color: var(--color-surface-page);
    color: var(--color-ink-2);
  }

  .main {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
    overflow-y: auto;
  }

  /* Section headers (layout look §4.1): 24 px rows, 12 px muted labels, 28 px actions. */
  .section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    block-size: 24px;
    padding-inline: 14px 6px;
  }

  .section-label {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .section-action {
    display: grid;
    place-items: center;
    inline-size: 28px;
    block-size: 28px;
    border-radius: 8px;
    color: var(--color-gray-300);
    /* 100 ms, as measured on the running app's section buttons. */
    --interact-duration: var(--duration-instant);
  }

  .section-action:hover {
    color: var(--color-gray-500);
  }

  :global([data-theme='dark']) .section-label {
    color: var(--color-gray-500);
  }

  :global([data-theme='dark']) .section-action {
    color: var(--color-gray-600);
  }

  /* The run marker slot keeps titles aligned: 20 px with 8 px after the 12 px glyph. */
  .marker {
    display: grid;
    flex-shrink: 0;
    place-items: center start;
    inline-size: 20px;
    block-size: 20px;
  }

  .direct {
    margin-inline-start: 4px;
    inline-size: 4px;
    block-size: 4px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-400);
  }

  .title {
    flex: 1;
    text-align: start;
  }

  .row-wrap {
    position: relative;
  }

  /* 20 px, 10 px in from the row's end, 6 px down: measured on the running app. */
  .row-more {
    position: absolute;
    inset-block-start: 6px;
    inset-inline-end: 10px;
    display: grid;
    place-items: center;
    inline-size: 20px;
    block-size: 20px;
    border-radius: var(--radius-tight);
    color: var(--color-ink-2);
  }

  .row-wrap:not(:hover, :focus-within) .row-more:not([data-current]) {
    opacity: 0;
  }

  .row-more:hover {
    color: var(--color-ink-1);
  }

  .row-wrap:is(:hover, :focus-within) .ago {
    opacity: 0;
  }

  .row-more:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .chats {
    display: flex;
    flex-direction: column;
    padding-inline: 6px;
  }

  .ago {
    flex-shrink: 0;
    padding-inline-start: var(--spacing-2);
    color: var(--color-ink-3);
    font-size: var(--text-nano);
    transition: opacity var(--duration-interact) var(--ease-standard);
  }
</style>
