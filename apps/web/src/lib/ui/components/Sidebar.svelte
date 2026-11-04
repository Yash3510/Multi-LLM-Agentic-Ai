<script lang="ts" module>
  import type { PathnameWithSearchOrHash } from '$app/types';
  import type { IconName } from '$lib/ui/icons/generated/icons';

  export type Destination = {
    href: PathnameWithSearchOrHash;
    label: string;
    icon: IconName;
  };
</script>

<script lang="ts">
  // The sidebar frame (layout look §3): open, a 245 px panel with the header row, New Chat, Search,
  // the pinned destinations, the caller's lists and the user button; closed, the 42 px rail with
  // the same actions as icons. Drawn in the premium look (ADR-0041 amendment): 18 px Phosphor
  // icons in muted grey, rows that take the soft tint on hover and a firmer tint with a hairline
  // when current. Resizing and the phone drawer are planned.
  import { resolve } from '$app/paths';
  import type { Snippet } from 'svelte';
  import { m } from '$lib/i18n/generated/messages.js';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import IconButton from './IconButton.svelte';
  import Logomark from './Logomark.svelte';
  import { sidebarWidth } from './sidebar-width';

  type Props = {
    open?: boolean;
    productName: string;
    userName: string;
    destinations: Destination[];
    /** The path of the page on screen, to mark its destination current. */
    current?: string;
    width?: number;
    onnewchat?: () => void;
    onsearch?: () => void;
    onusermenu?: () => void;
    /** The sections and lists below the primary rows. */
    children?: Snippet;
  };

  let {
    open = $bindable(true),
    productName,
    userName,
    destinations,
    current,
    width,
    onnewchat,
    onsearch,
    onusermenu,
    children,
  }: Props = $props();

  export function isOpen() {
    return open;
  }

  const panelWidth = $derived(sidebarWidth(width));
  const userInitials = $derived(
    userName
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join(''),
  );
  const isCurrent = (href: string) => current !== undefined && href === current;
</script>

<nav
  aria-label={m.nav_label()}
  class="sidebar"
  data-open={open ? '' : undefined}
  style:--sidebar-width="{panelWidth}px"
>
  {#if open}
    <div class="panel">
      <div class="head">
        <a class="logo" href={resolve('/')} aria-label={productName}>
          <span class="mark"><Logomark size={22} /></span>
        </a>
        <a class="name" href={resolve('/')}>{productName}</a>
        <IconButton
          icon="sidebar-simple"
          label={m.shell_close_sidebar()}
          onclick={() => (open = false)}
        />
      </div>

      <div class="scroll">
        <div class="primary">
          <button type="button" class="row" onclick={onnewchat}>
            <span class="glyph"><Icon name="new-chat" size={18} /></span>
            {m.shell_new_chat()}
          </button>
          <button type="button" class="row" onclick={onsearch}>
            <span class="glyph"><Icon name="magnifying-glass" size={18} /></span>
            {m.shell_search()}
          </button>
          {#each destinations as destination (destination.href)}
            <a
              class="row"
              href={resolve(destination.href)}
              data-current={isCurrent(destination.href) ? '' : undefined}
              aria-current={isCurrent(destination.href) ? 'page' : undefined}
            >
              <span class="glyph"><Icon name={destination.icon} size={18} /></span>
              {destination.label}
            </a>
          {/each}
        </div>
        {@render children?.()}
      </div>

      <div class="foot">
        <button
          type="button"
          class="row user"
          aria-label={`${m.shell_user_menu()}: ${userName}`}
          onclick={onusermenu}
        >
          <span class="avatar" aria-hidden="true">{userInitials}</span>
          <span class="truncate">{userName}</span>
        </button>
      </div>
    </div>
  {:else}
    <div class="rail">
      <div class="rail-group">
        <button
          type="button"
          class="rail-open"
          aria-label={m.shell_open_sidebar()}
          onclick={() => (open = true)}
        >
          <span class="mark"><Logomark size={22} /></span>
          <span class="open-glyph" aria-hidden="true"><Icon name="sidebar-simple" size={18} /></span
          >
        </button>
        <IconButton icon="new-chat" label={m.shell_new_chat()} onclick={onnewchat} />
        <IconButton icon="magnifying-glass" label={m.shell_search()} onclick={onsearch} />
        {#each destinations as destination (destination.href)}
          <a
            class="rail-link"
            href={resolve(destination.href)}
            aria-label={destination.label}
            title={destination.label}
            data-current={isCurrent(destination.href) ? '' : undefined}
            aria-current={isCurrent(destination.href) ? 'page' : undefined}
          >
            <Icon name={destination.icon} size={18} />
          </a>
        {/each}
      </div>
      <button
        type="button"
        class="rail-user"
        aria-label={`${m.shell_user_menu()}: ${userName}`}
        onclick={onusermenu}
      >
        <span class="avatar" aria-hidden="true">{userInitials}</span>
      </button>
    </div>
  {/if}
</nav>

<style>
  .sidebar {
    flex-shrink: 0;
    inline-size: 42px;
    block-size: 100%;
    overflow: hidden;
    background-color: var(--color-surface-sunken);
    box-shadow: inset -1px 0 0 var(--color-hair);
    color: var(--color-ink-2);
    font-size: var(--text-small);
    line-height: var(--text-small--line-height);
    user-select: none;
    transition: inline-size 250ms cubic-bezier(0.22, 1, 0.36, 1);
  }

  .sidebar[data-open] {
    inline-size: var(--sidebar-width);
  }

  /* The panel keeps its full width while the frame animates, so content is clipped, not
     reflowed. */
  .panel {
    display: flex;
    flex-direction: column;
    inline-size: var(--sidebar-width);
    block-size: 100%;
  }

  .head {
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
    padding: 6px var(--spacing-1) var(--spacing-1);
  }

  .logo {
    display: grid;
    place-items: center;
    inline-size: 34px;
    block-size: 32px;
    border-radius: var(--radius-inset);
  }

  .mark {
    display: inline-grid;
    place-items: center;
    transition: opacity 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .name {
    flex: 1;
    min-inline-size: 0;
    padding-inline: 2px;
    color: var(--color-ink-2);
    font-size: var(--text-ui);
    text-decoration: none;
  }

  .scroll {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 6px;
    min-block-size: 0;
    padding-block: 10px;
    overflow-y: auto;
    scrollbar-width: none;
  }

  .scroll:hover {
    scrollbar-width: thin;
  }

  .primary {
    display: flex;
    flex-direction: column;
    padding-inline: var(--spacing-1);
    padding-block-end: var(--spacing-1);
  }

  .row {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    inline-size: 100%;
    padding: 6px var(--spacing-2);
    border-radius: var(--radius-inset);
    color: var(--color-ink-2);
    text-align: start;
    text-decoration: none;
    transition:
      background-color 150ms cubic-bezier(0.4, 0, 0.2, 1),
      color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Icons are muted and darken with the row. */
  .glyph {
    display: inline-flex;
    color: var(--color-gray-600);
    transition: color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global([data-theme='dark']) .glyph {
    color: var(--color-gray-400);
  }

  @media (hover: hover) {
    .row:hover {
      background-color: var(--color-tint);
      color: var(--color-ink-1);
    }

    .row:hover .glyph {
      color: var(--color-ink-1);
    }
  }

  .row[data-current] {
    background-color: var(--color-tint);
    box-shadow: var(--shadow-hairline);
    color: var(--color-ink-1);
  }

  .row[data-current] .glyph {
    color: var(--color-ink-1);
  }

  :is(.row, .logo, .name, .rail-open, .rail-link, .rail-user):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .foot {
    padding: var(--spacing-1) var(--spacing-1) 6px;
  }

  .user {
    gap: var(--spacing-3);
    padding: 6px;
  }

  .avatar {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 22px;
    block-size: 22px;
    border-radius: var(--radius-pill);
    background-color: var(--color-track);
    color: var(--color-ink-2);
    font-size: var(--text-nano);
    font-weight: var(--font-weight-medium);
  }

  .rail {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    block-size: 100%;
    padding: var(--spacing-1);
  }

  .rail-group {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }

  .rail-open,
  .rail-link,
  .rail-user {
    display: grid;
    place-items: center;
    inline-size: 32px;
    block-size: 32px;
    border-radius: var(--radius-control);
    color: var(--color-gray-600);
    transition:
      background-color 150ms cubic-bezier(0.4, 0, 0.2, 1),
      color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .rail-open {
    margin-block-end: var(--spacing-1);
    cursor: e-resize;
  }

  :global([data-theme='dark']) :is(.rail-open, .rail-link, .rail-user) {
    color: var(--color-gray-400);
  }

  /* On hover the mark gives way to the sidebar glyph, as in the measured rail. */
  .rail-open > * {
    grid-area: 1 / 1;
  }

  .open-glyph {
    display: inline-flex;
    opacity: 0;
  }

  @media (hover: hover) {
    :is(.rail-open, .rail-link, .rail-user):hover {
      background-color: var(--color-tint);
      color: var(--color-ink-1);
    }

    .rail-open:hover .mark {
      opacity: 0;
    }

    .rail-open:hover .open-glyph {
      opacity: 1;
    }
  }

  .rail-link[data-current] {
    background-color: var(--color-tint);
    box-shadow: var(--shadow-hairline);
    color: var(--color-ink-1);
  }

  @media (prefers-reduced-motion: reduce) {
    .sidebar {
      transition-duration: 1ms;
    }
  }
</style>
