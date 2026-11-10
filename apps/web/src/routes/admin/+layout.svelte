<script lang="ts">
  // The admin frame (admin look §3): the link strip (Users, Evaluations, Functions, Settings)
  // over the scrolling content. Settings opens the settings dialog, as on the running app.
  import { page } from '$app/state';
  import { resolve } from '$app/paths';
  import { useOpenSettings } from '$lib/ui/settings-context';

  let { children } = $props();

  const openSettings = useOpenSettings();
  const section = $derived(page.url.pathname.split('/')[2] ?? 'users');
</script>

<svelte:head><title>Admin Panel / 4CE</title></svelte:head>

<div class="admin">
  <header class="bar" data-page-bar>
    <nav class="links" aria-label="Admin">
      <a
        href={resolve('/admin/users/[tab]', { tab: 'overview' })}
        aria-current={section === 'users' ? 'page' : undefined}
        draggable="false">Users</a
      >
      <a
        href={resolve('/admin/evaluations')}
        aria-current={section === 'evaluations' ? 'page' : undefined}
        draggable="false">Evaluations</a
      >
      <a
        href={resolve('/admin/functions')}
        aria-current={section === 'functions' ? 'page' : undefined}
        draggable="false">Functions</a
      >
      <button type="button" onclick={() => openSettings?.()}>Settings</button>
    </nav>
  </header>
  <div class="content">{@render children()}</div>
</div>

<style>
  .admin {
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
    block-size: 100%;
  }

  .bar {
    padding: 8px 10px 4px;
    backdrop-filter: blur(24px);
    user-select: none;
  }

  .links {
    display: flex;
    align-items: center;
    gap: 2px;
    margin-inline-end: 6px;
    padding-block: 4px;
    overflow-x: auto;
    scrollbar-width: none;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  @media (min-width: 48rem) {
    .links {
      gap: 4px;
    }
  }

  .links :is(a, button) {
    flex-shrink: 0;
    padding-inline: 4px;
    color: var(--color-gray-300);
    font-size: var(--text-ui);
    transition: color 150ms;
  }

  .links :is(a, button):hover {
    color: var(--color-gray-700);
  }

  .links a[aria-current] {
    color: inherit;
  }

  :global([data-theme='dark']) .links :is(a, button) {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .links :is(a, button):hover {
    color: var(--color-white);
  }

  :global([data-theme='dark']) .links a[aria-current] {
    color: inherit;
  }

  .links :is(a, button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }

  .content {
    flex: 1;
    min-inline-size: 0;
    padding-block-end: 4px;
    overflow: hidden auto;
  }
</style>
