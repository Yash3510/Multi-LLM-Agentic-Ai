<script lang="ts">
  // People (admin look §4): the Overview and Groups tabs with their counts, beside the content.
  import { resolve } from '$app/paths';
  import { data as source } from '$lib/data';
  import PeopleList from '$lib/ui/components/PeopleList.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  let counts = $state<{ people: number; groups: number }>();
  let version = $state(0);

  $effect(() => {
    void version;
    void source.listUsers().then((people) => (counts = { people: people.length, groups: 0 }));
  });
</script>

<div class="people-shell">
  <nav class="tabs" aria-label="People">
    <a
      href={resolve('/admin/users/[tab]', { tab: 'overview' })}
      aria-current={data.tab === 'overview' ? 'page' : undefined}
      draggable="false"
      >Overview{#if counts}<span class="count">{counts.people.toLocaleString()}</span>{/if}</a
    >
    <a
      href={resolve('/admin/users/[tab]', { tab: 'groups' })}
      aria-current={data.tab === 'groups' ? 'page' : undefined}
      draggable="false"
      >Groups{#if counts}<span class="count">{counts.groups.toLocaleString()}</span>{/if}</a
    >
  </nav>
  <div class="pane">
    {#if data.tab === 'overview'}
      <PeopleList {source} {version} />
    {/if}
  </div>
</div>

<style>
  .people-shell {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    block-size: 100%;
    padding-block-end: 8px;
  }

  @media (min-width: 64rem) {
    .people-shell {
      flex-direction: row;
    }
  }

  .tabs {
    display: flex;
    gap: 10px;
    margin-inline: 8px;
    padding-inline: 8px;
    overflow-x: auto;
    scrollbar-width: none;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  @media (min-width: 40rem) {
    .tabs {
      margin-inline: 10px;
    }
  }

  @media (min-width: 64rem) {
    .tabs {
      flex: none;
      flex-direction: column;
      gap: 0;
      inline-size: 200px;
      margin: 0;
      padding-inline: 10px;
    }
  }

  :global([data-theme='dark']) .tabs {
    color: var(--color-gray-200);
  }

  .tabs a {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    padding: 4px 2px;
    border-radius: 8px;
    color: var(--color-gray-300);
    user-select: none;
    transition: color 150ms;
  }

  .tabs a:hover {
    color: var(--color-gray-700);
  }

  .tabs a[aria-current] {
    color: inherit;
  }

  :global([data-theme='dark']) .tabs a {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .tabs a:hover {
    color: var(--color-white);
  }

  :global([data-theme='dark']) .tabs a[aria-current] {
    color: inherit;
  }

  .count {
    opacity: 0.6;
  }

  .tabs a:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }

  .pane {
    flex: 1;
    padding-inline: 14px;
    overflow-y: scroll;
  }

  @media (min-width: 64rem) {
    .pane {
      padding-inline: 0 16px;
    }
  }
</style>
