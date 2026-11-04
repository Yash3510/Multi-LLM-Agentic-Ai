<script module lang="ts">
  import type { SectionMeta } from '../section';

  // English until the ui_section_shell and ui_shell_* messages exist; the captions below are the
  // same. Demo data is sector-neutral: rules R2 to R6, ids like CASE-0142.
  export const section: SectionMeta = {
    id: 'shell',
    title: () => 'Shell',
    description: () =>
      'The sidebar, its closed rail and the top bar, drawn in a frame the size of a small window.',
  };
</script>

<script lang="ts">
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import GroupHeading from '$lib/ui/components/GroupHeading.svelte';
  import IconButton from '$lib/ui/components/IconButton.svelte';
  import ListRow from '$lib/ui/components/ListRow.svelte';
  import Menu from '$lib/ui/components/Menu.svelte';
  import type { MenuEntry } from '$lib/ui/components/menu-model';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Sidebar, { type Destination } from '$lib/ui/components/Sidebar.svelte';
  import TopBar from '$lib/ui/components/TopBar.svelte';
  import { formatAgo, toIntlLocale } from '$lib/ui/format';

  const locale = toIntlLocale(getLocale());
  const NOW = new Date(2026, 10, 4, 10, 30);
  const hoursAgo = (hours: number) => new Date(NOW.getTime() - hours * 3_600_000);

  const DESTINATIONS: Destination[] = [
    { href: '/ui#shell', label: 'Notes', icon: 'note' },
    { href: '/ui#lists', label: 'Workspace', icon: 'workspace' },
  ];

  const TODAY = [
    { id: 'CASE-0142', title: 'R2 · Ratio check', at: hoursAgo(1) },
    { id: 'CASE-0143', title: 'R3 · Duration review', at: hoursAgo(5) },
  ];
  const YESTERDAY = [{ id: 'CASE-0139', title: 'R4 · Cost of the second batch', at: hoursAgo(26) }];

  let open = $state(true);

  // The chat menu, row for row as the running app shows it (layout look §4.5).
  const CHAT_MENU: MenuEntry[] = [
    { id: 'share', label: 'Share', icon: 'share' },
    { id: 'download', label: 'Download', icon: 'download-simple' },
    { id: 'rename', label: 'Rename', icon: 'rename' },
    { id: 'unread', label: 'Mark as unread', icon: 'mark-unread' },
    { type: 'separator' },
    { id: 'pin', label: 'Pin', icon: 'pin' },
    { id: 'clone', label: 'Clone', icon: 'copy' },
    { id: 'archive', label: 'Archive', icon: 'archive' },
    { id: 'delete', label: 'Delete', icon: 'trash', danger: true },
  ];
</script>

<div class="flex flex-col gap-10">
  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Sidebar and top bar</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          18 px muted icons that darken on the soft tint; rows 32 px; the open case is current. The
          sidebar button closes it to the rail
        </dt>
        <dd>
          <div class="window">
            <Sidebar
              bind:open
              productName="4CE"
              userName="Asha Rao"
              destinations={DESTINATIONS}
              current="/ui#shell"
            >
              <div class="lists">
                <GroupHeading group={{ band: 'today' }} first variant="sidebar" level={4} />
                {#each TODAY as chat (chat.id)}
                  {@render chatRow(chat, chat.id === 'CASE-0143')}
                {/each}
                <GroupHeading group={{ band: 'yesterday' }} variant="sidebar" level={4} />
                {#each YESTERDAY as chat (chat.id)}
                  {@render chatRow(chat, false)}
                {/each}
              </div>
            </Sidebar>
            <div class="main">
              <TopBar title="R3 · Duration review" onchatactions={() => {}}>
                {#snippet end()}
                  <IconButton icon="temporary-chat" label="Temporary Chat" />
                  <IconButton icon="controls" label="Controls" />
                {/snippet}
              </TopBar>
            </div>
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>Closed: the 42 px rail. The mark gives way to the sidebar glyph on hover</dt>
        <dd>
          <div class="window narrow">
            <Sidebar
              open={false}
              productName="4CE"
              userName="Asha Rao"
              destinations={DESTINATIONS}
              current="/ui#shell"
            />
            <div class="main">
              <TopBar />
            </div>
          </div>
        </dd>
      </div>
    </dl>
  </div>
</div>

{#snippet chatRow(chat: { id: string; title: string; at: Date }, current: boolean)}
  <ListRow href={current ? undefined : '/ui#shell'} variant="sidebar" {current}>
    <span class="truncate">{chat.title}</span>
    {#if current}
      <Menu label="Chat Menu" items={CHAT_MENU} backLabel="Back" align="start">
        {#snippet trigger({ props })}
          <button {...props} class="row-more" aria-label="Chat Menu">
            <Icon name="row-more" size={14} />
          </button>
        {/snippet}
      </Menu>
    {:else}
      <time class="ago" datetime={chat.at.toISOString()}>
        {formatAgo(chat.at, { now: NOW, locale })}
      </time>
    {/if}
  </ListRow>
{/snippet}

<style>
  /* Caption on the left, examples on the right; stacked when narrow. */
  .rows {
    display: flex;
    flex-direction: column;
  }

  .row {
    display: grid;
    gap: var(--spacing-2) var(--spacing-6);
    padding-block: var(--spacing-3);
    border-top: 1px solid var(--color-line-1);
  }

  @media (min-width: 48rem) {
    .row {
      grid-template-columns: 14rem minmax(0, 1fr);
      align-items: start;
    }
  }

  dt {
    font-size: var(--text-caption);
    line-height: var(--text-caption--line-height);
    color: var(--color-ink-3);
  }

  dd {
    min-width: 0;
  }

  /* A small window: the frame clips like the real viewport. */
  .window {
    display: flex;
    block-size: 26rem;
    overflow: hidden;
    border-radius: var(--radius-card);
    background-color: var(--color-surface-page);
    box-shadow: var(--shadow-e1);
  }

  .window.narrow {
    block-size: 18rem;
  }

  .main {
    flex: 1;
    min-inline-size: 0;
  }

  .lists {
    display: flex;
    flex-direction: column;
    padding-inline: 6px;
  }

  /* The row's more button (layout look §4.4): 20 px, a 14 px bold glyph, muted until hovered. */
  .row-more {
    position: relative;
    z-index: 1;
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 20px;
    block-size: 20px;
    border-radius: var(--radius-tight);
    color: var(--color-gray-600);
  }

  .row-more:hover {
    color: var(--color-ink-1);
  }

  .row-more:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .ago {
    flex-shrink: 0;
    padding-inline-start: var(--spacing-2);
    color: var(--color-ink-3);
    font-size: var(--text-nano);
  }
</style>
