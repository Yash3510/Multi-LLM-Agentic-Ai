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
  // the same actions as icons. Matches the running app exactly (layout look §3): 16 px icons in
  // the row ink, a gray-100 hover and a 3.5 % black fill on the current row. Resizing and the
  // phone drawer are planned.
  import { resolve } from '$app/paths';
  import { appHref } from '$lib/ui/app-href';
  import type { Snippet } from 'svelte';
  import { m } from '$lib/i18n/generated/messages.js';
  import Icon from '$lib/ui/icons/Icon.svelte';
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
    /** Opens the user menu from the pressed avatar. */
    onusermenu?: (event: MouseEvent) => void;
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
  // A destination stays current on the pages under it (the workspace's tabs and editors), as the
  // running app's rail does.
  const isCurrent = (href: string) =>
    current !== undefined &&
    (href === current || (href !== '/' && !href.includes('#') && current.startsWith(`${href}/`)));
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
          <span class="mark" data-intro-logo><Logomark size={22} /></span>
        </a>
        <a class="name" href={resolve('/')}>{productName}</a>
        <button
          type="button"
          class="closer"
          aria-label={m.shell_close_sidebar()}
          title={m.shell_close_sidebar()}
          onclick={() => (open = false)}
        >
          <Icon name="sidebar-simple" size={16} />
        </button>
      </div>

      <div class="scroll">
        <div class="primary">
          <button type="button" class="row" onclick={onnewchat}>
            <span class="glyph"><Icon name="new-chat" size={16} /></span>
            {m.shell_new_chat()}
          </button>
          <button type="button" class="row" onclick={onsearch}>
            <span class="glyph"><Icon name="magnifying-glass" size={16} /></span>
            {m.shell_search()}
          </button>
          {#each destinations as destination (destination.href)}
            <a
              class="row"
              href={appHref(destination.href)}
              data-current={isCurrent(destination.href) ? '' : undefined}
              aria-current={isCurrent(destination.href) ? 'page' : undefined}
            >
              <span class="glyph"><Icon name={destination.icon} size={16} /></span>
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
          <span class="avatar" aria-hidden="true">{userInitials}<span class="presence"></span></span
          >
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
          <span class="mark" data-intro-logo><Logomark size={22} /></span>
          <span class="open-glyph" aria-hidden="true"><Icon name="sidebar-simple" size={16} /></span
          >
        </button>
        <button
          type="button"
          class="rail-link"
          aria-label={m.shell_new_chat()}
          title={m.shell_new_chat()}
          onclick={onnewchat}
        >
          <Icon name="new-chat" size={16} />
        </button>
        <button
          type="button"
          class="rail-link"
          aria-label={m.shell_search()}
          title={m.shell_search()}
          onclick={onsearch}
        >
          <Icon name="magnifying-glass" size={16} />
        </button>
        {#each destinations as destination (destination.href)}
          <a
            class="rail-link"
            href={appHref(destination.href)}
            aria-label={destination.label}
            title={destination.label}
            data-current={isCurrent(destination.href) ? '' : undefined}
            aria-current={isCurrent(destination.href) ? 'page' : undefined}
          >
            <Icon name={destination.icon} size={16} />
          </a>
        {/each}
      </div>
      <button
        type="button"
        class="rail-user"
        aria-label={`${m.shell_user_menu()}: ${userName}`}
        onclick={onusermenu}
      >
        <span class="avatar" aria-hidden="true">{userInitials}<span class="presence"></span></span>
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

  /* The closed rail sits on the page ground with a near-invisible edge (layout look §3.5). */
  .sidebar:not([data-open]) {
    background-color: var(--color-surface-page);
    box-shadow: inset -0.5px 0 0 color-mix(in srgb, var(--color-gray-50) 30%, transparent);
  }

  :global([data-theme='dark']) .sidebar:not([data-open]) {
    box-shadow: inset -0.5px 0 0 color-mix(in srgb, var(--color-gray-850) 30%, transparent);
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
    /* End padding measured: the running app's header, list and footer stop short of the edge by
       9, 14 and 5 px (its scrollbar lane). */
    padding: 6px 9px var(--spacing-1) var(--spacing-1);
    /* Overlaps the list by 8 px (layout look §3.6). */
    margin-block-end: calc(var(--spacing-2) * -1);
  }

  .closer {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 30px;
    block-size: 30px;
    border-radius: 8px;
    color: var(--color-gray-600);
    cursor: w-resize;
    transition: background-color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global([data-theme='dark']) .closer {
    color: var(--color-gray-400);
  }

  .logo {
    display: grid;
    place-items: center;
    inline-size: 34px;
    block-size: 30px;
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
    padding-inline-end: var(--spacing-2);
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

  .glyph {
    display: inline-flex;
  }

  @media (hover: hover) {
    :is(.row, .closer, .logo):hover {
      background-color: var(--color-row-hover);
    }
  }

  .row[data-current] {
    background-color: var(--color-row-current);
  }

  :is(.row, .logo, .name, .closer, .rail-open, .rail-link, .rail-user):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .foot {
    padding: var(--spacing-1) 5px 6px var(--spacing-1);
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

  /* Presence (layout look §3.10): a green dot with a 2 px ring at the avatar's lower end. */
  .avatar {
    position: relative;
  }

  .presence {
    position: absolute;
    inset-block-end: -2px;
    inset-inline-end: -2px;
    inline-size: 10px;
    block-size: 10px;
    border: 2px solid var(--color-white);
    border-radius: var(--radius-pill);
    background-color: var(--color-green-500);
  }

  :global([data-theme='dark']) .presence {
    border-color: var(--color-gray-900);
  }

  .rail {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    block-size: 100%;
    padding: var(--spacing-1);
  }

  /* Rail (layout look §3.5): 32 px targets stacked with no gap under a 34 px logo slot. */
  .rail-group {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .rail-open,
  .rail-link,
  .rail-user {
    display: grid;
    place-items: center;
    inline-size: 32px;
    block-size: 32px;
    border-radius: 8px;
    color: inherit;
    transition:
      background-color 150ms cubic-bezier(0.4, 0, 0.2, 1),
      color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .rail-open {
    inline-size: 34px;
    block-size: 30px;
    margin-block: 2px 6px;
    cursor: e-resize;
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
      background-color: var(--color-row-hover);
    }

    .rail-open:hover .mark {
      opacity: 0;
    }

    .rail-open:hover .open-glyph {
      opacity: 1;
    }
  }

  .rail-link[data-current] {
    background-color: var(--color-row-current);
  }

  /* Below 768 px the running app drops the rail for a lone sidebar button in the corner, and
     the open sidebar lies over the page instead of pushing it. */
  @media (max-width: 47.99rem) {
    /* Raised over the sticky top bar (z-index 30) so the corner button can be tapped. */
    .sidebar:not([data-open]) {
      position: relative;
      z-index: 40;
      inline-size: 0;
      overflow: visible;
      box-shadow: none;
    }

    .sidebar[data-open] {
      position: fixed;
      inset-block: 0;
      inset-inline-start: 0;
      z-index: 50;
    }

    .rail {
      position: fixed;
      inset-block-start: 0;
      inset-inline-start: 0;
      z-index: 10;
      block-size: auto;
      padding: 6px 8px;
    }

    .rail > :not(.rail-group),
    .rail-group > :not(.rail-open),
    .rail-open .mark {
      display: none;
    }

    .rail-open .open-glyph {
      opacity: 1;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .sidebar {
      transition-duration: 1ms;
    }
  }
</style>
