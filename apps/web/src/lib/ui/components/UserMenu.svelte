<script lang="ts">
  // The user menu (layout look §7.1, F125 to F132): the person with the active count, their
  // status, the destinations, then Playground, Admin Panel (admins), Settings and Sign Out. It opens upward from the
  // avatar that was pressed and uses the shared menu card (common look F12).
  import { DropdownMenu } from 'bits-ui';
  import { resolve } from '$app/paths';
  import type { User } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './menu.css';
  import './surfaces.css';

  type Props = {
    open: boolean;
    user: User;
    /** How many people are signed in now. */
    active: number;
    /** The avatar the menu hangs from. */
    anchor?: HTMLElement;
    onsettings: () => void;
    onstatus: () => void;
    onsignout: () => void;
  };

  let {
    open = $bindable(),
    user,
    active,
    anchor,
    onsettings,
    onstatus,
    onsignout,
  }: Props = $props();

  const initials = $derived(
    user.name
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join(''),
  );
</script>

<DropdownMenu.Root bind:open>
  <DropdownMenu.Portal>
    <DropdownMenu.Content
      class="user-menu"
      data-menu
      data-surface="float"
      side="top"
      align="start"
      sideOffset={4}
      alignOffset={11}
      customAnchor={anchor}
    >
      <DropdownMenu.Item class="identity" data-menu-row>
        <span class="avatar" aria-hidden="true">{initials}</span>
        <span class="name">{user.name}</span>
        <span class="active" title="Active Users"><span class="dot"></span>{active}</span>
      </DropdownMenu.Item>
      <DropdownMenu.Item class="status" data-menu-row onSelect={onstatus}>
        <span data-menu-lead class="lead"><Icon name="smiley" size={14} /></span>
        <span class="name">{user.status?.message || 'Update your status'}</span>
      </DropdownMenu.Item>
      <DropdownMenu.Separator data-menu-separator />
      <DropdownMenu.Item data-menu-row>
        {#snippet child({ props })}
          <a {...props} href={resolve('/workspace')}
            ><span data-menu-lead><Icon name="workspace" size={14} /></span>Workspace</a
          >
        {/snippet}
      </DropdownMenu.Item>
      <DropdownMenu.Separator data-menu-separator />
      <DropdownMenu.Item data-menu-row>
        {#snippet child({ props })}
          <a {...props} href={resolve('/playground')}
            ><span data-menu-lead><Icon name="code" size={14} /></span>Playground</a
          >
        {/snippet}
      </DropdownMenu.Item>
      {#if user.role === 'admin'}
        <DropdownMenu.Item data-menu-row>
          {#snippet child({ props })}
            <a {...props} href={resolve('/admin')}
              ><span data-menu-lead><Icon name="user" size={14} /></span>Admin Panel</a
            >
          {/snippet}
        </DropdownMenu.Item>
      {/if}
      <DropdownMenu.Item data-menu-row onSelect={onsettings}>
        <span data-menu-lead><Icon name="gear-six" size={14} /></span>Settings
      </DropdownMenu.Item>
      <DropdownMenu.Item data-menu-row onSelect={onsignout}>
        <span data-menu-lead><Icon name="sign-out" size={14} /></span>Sign Out
      </DropdownMenu.Item>
    </DropdownMenu.Content>
  </DropdownMenu.Portal>
</DropdownMenu.Root>

<style>
  /* As wide as the open sidebar less 16 px (layout look §7.1). */
  :global(.user-menu) {
    z-index: 9999;
    inline-size: 240px;
  }

  /* The person and status rows use 12 px text and an 18 px lead. */
  :global(.user-menu .identity),
  :global(.user-menu .status) {
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .avatar {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 18px;
    block-size: 18px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-200);
    color: var(--color-gray-700);
    font-size: 8px;
  }

  .lead {
    justify-content: center;
    inline-size: 18px;
  }

  .name {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .active {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 6px;
    color: var(--color-gray-500);
    font-size: var(--text-micro);
    line-height: 1;
  }

  :global([data-theme='dark']) .active {
    color: var(--color-gray-400);
  }

  .dot {
    inline-size: 6px;
    block-size: 6px;
    border-radius: var(--radius-pill);
    background-color: var(--color-green-500);
  }
</style>
