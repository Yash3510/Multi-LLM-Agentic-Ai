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
  import type { ChatSummary } from '$lib/data';

  let { children, chats }: { children: Snippet; chats: ChatSummary[] } = $props();

  const locale = toIntlLocale(getLocale());
  // Planned routes (web-screens.md); the hash keeps them typed until they exist.
  const DESTINATIONS: Destination[] = [
    { href: '/#notes', label: 'Notes', icon: 'note' },
    { href: '/#workspace', label: 'Workspace', icon: 'workspace' },
  ];

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

  let open = $state(true);

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
    userName="Asha Rao"
    destinations={DESTINATIONS}
    current={page.url.pathname + page.url.hash}
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
          {#if page.url.pathname === `/c/${row.id}`}
            <!-- The open chat shows its menu button in place of the time (layout look §4.4). -->
            <button type="button" class="row-more" aria-label="Chat Menu" title="More">
              <Icon name="row-more" size={14} />
            </button>
          {/if}
        </div>
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
    transition: color 100ms;
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
  }
</style>
