<script lang="ts">
  import Toaster from '$lib/ui/components/Toaster.svelte';
  import '../app.css';
  import { onMount } from 'svelte';
  import { onNavigate } from '$app/navigation';
  import { page } from '$app/state';
  import AppShell from '$lib/ui/components/AppShell.svelte';
  import { removeSplash } from '$lib/ui/splash';
  import type { LayoutProps } from './$types';

  let { children, data }: LayoutProps = $props();

  onMount(removeSplash);

  // Routes crossfade where the browser has view transitions (ADR-0042). Only the page is named,
  // and only while it changes, so the sidebar stays still and nothing is restacked at rest.
  onNavigate((navigation) => {
    if (!document.startViewTransition) return;
    if (navigation.from?.url.pathname === navigation.to?.url.pathname) return;
    const root = document.documentElement;
    return new Promise((resolve) => {
      root.setAttribute('data-routing', '');
      const transition = document.startViewTransition(async () => {
        resolve();
        await navigation.complete;
      });
      void transition.finished.finally(() => root.removeAttribute('data-routing'));
    });
  });

  // The design reference draws its own page; every other screen sits in the app shell.
  const bare = $derived(
    page.route.id === '/auth' ||
      page.route.id === '/error' ||
      (page.route.id?.startsWith('/ui') ?? false),
  );
</script>

{#if bare}
  {@render children()}
{:else}
  <AppShell chats={data.chats} userName={data.user?.name ?? ''} user={data.user}
    >{@render children()}</AppShell
  >
{/if}

<Toaster />
