<script lang="ts">
  // The signed-in frame (layout look §2.1, §3): the sidebar beside the main area, full viewport
  // height. Chats are stand-ins until the chat API lands; pinned destinations point at planned
  // routes.
  import { page } from '$app/state';
  import { m } from '$lib/i18n/generated/messages.js';
  import { DEMO_CHATS } from '$lib/demo/chats';
  import GroupHeading from './GroupHeading.svelte';
  import ListRow from './ListRow.svelte';
  import Sidebar, { type Destination } from './Sidebar.svelte';
  import { formatAgo, timeGroup, toIntlLocale } from '$lib/ui/format';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();

  const locale = toIntlLocale(getLocale());
  // Planned routes (web-screens.md); the hash keeps them typed until they exist.
  const DESTINATIONS: Destination[] = [
    { href: '/#notes', label: 'Notes', icon: 'note' },
    { href: '/#workspace', label: 'Workspace', icon: 'workspace' },
  ];

  const rows = DEMO_CHATS.map((chat, index) => {
    const group = timeGroup(chat.updated);
    const before = index > 0 ? timeGroup(DEMO_CHATS[index - 1].updated) : undefined;
    return {
      ...chat,
      heading: JSON.stringify(group) === JSON.stringify(before) ? undefined : group,
    };
  });

  let open = $state(true);
</script>

<div class="frame">
  <Sidebar
    bind:open
    productName={m.app_name()}
    userName="Asha Rao"
    destinations={DESTINATIONS}
    current={page.url.pathname + page.url.hash}
  >
    <div class="chats">
      {#each rows as row, index (row.id)}
        {#if row.heading}
          <GroupHeading group={row.heading} first={index === 0} variant="sidebar" />
        {/if}
        <ListRow
          href={`/c/${row.id}`}
          variant="sidebar"
          current={page.url.pathname === `/c/${row.id}`}
        >
          <span class="truncate">{row.title}</span>
          <time class="ago" datetime={row.updated.toISOString()}>
            {formatAgo(row.updated, { locale })}
          </time>
        </ListRow>
      {/each}
    </div>
  </Sidebar>
  <main id="main" class="main">
    {@render children()}
  </main>
</div>

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
  }
</style>
