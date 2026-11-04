<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import AppShell from '$lib/ui/components/AppShell.svelte';
  import { removeSplash } from '$lib/ui/splash';
  import type { LayoutProps } from './$types';

  let { children, data }: LayoutProps = $props();

  onMount(removeSplash);

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
  <AppShell chats={data.chats} userName={data.user?.name ?? ''}>{@render children()}</AppShell>
{/if}
