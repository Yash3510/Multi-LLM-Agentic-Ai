<script lang="ts">
  // Channels: the list, with New Channel and delete for admins (delete needs the name typed and
  // is logged).
  import { resolve } from '$app/paths';
  import type { Channel } from '$lib/data';
  import { data as source } from '$lib/data';
  import ConfirmDialog from '$lib/ui/components/ConfirmDialog.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  let channels = $state<Channel[]>([]);
  let name = $state('');
  let deleting = $state<Channel>();
  let typed = $state('');
  const admin = $derived(data.user?.role === 'admin');

  async function load() {
    channels = await source.listChannels();
  }
  void load();

  async function create(event: SubmitEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    await source.createChannel({ name, description: '' });
    name = '';
    await load();
  }

  async function remove() {
    if (!deleting) return;
    const id = deleting.id;
    deleting = undefined;
    typed = '';
    await source.deleteChannel(id);
    await load();
  }
</script>

<svelte:head><title>Channels / 4CE</title></svelte:head>

<div class="page">
  <h1>Channels <span class="count">{channels.length}</span></h1>
  {#if admin}
    <form class="new" onsubmit={create}>
      <input bind:value={name} placeholder="New channel name" aria-label="New channel name" />
      <button type="submit">New Channel</button>
    </form>
  {/if}
  <ul>
    {#each channels as channel (channel.id)}
      <li>
        <a href={resolve('/channels/[id]', { id: channel.id })}># {channel.name}</a>
        {#if admin}
          <button
            type="button"
            aria-label="Delete {channel.name}"
            onclick={() => (deleting = channel)}><Icon name="trash" size={14} /></button
          >
        {/if}
      </li>
    {:else}
      <li class="none">No channels yet.</li>
    {/each}
  </ul>
</div>

<ConfirmDialog
  open={deleting !== undefined}
  title="Delete #{deleting?.name}?"
  message="This deletes the channel and all its messages. Type its name to confirm."
  confirmLabel="Delete"
  confirmDisabled={typed.trim() !== deleting?.name}
  onconfirm={remove}
  oncancel={() => {
    deleting = undefined;
    typed = '';
  }}
>
  <input class="typed" bind:value={typed} placeholder={deleting?.name} aria-label="Channel name" />
</ConfirmDialog>

<style>
  .page {
    padding: 12px 14px;
    font-size: var(--text-ui);
  }
  h1 {
    display: flex;
    gap: 6px;
    margin-block-end: 8px;
    font-size: var(--text-ui);
    font-weight: 400;
  }
  .count {
    color: var(--color-gray-500);
  }
  .new {
    display: flex;
    gap: 8px;
    margin-block-end: 8px;
  }
  .new input {
    flex: 1;
    block-size: 32px;
    padding-inline: 8px;
    border: 1px solid var(--color-gray-100);
    border-radius: 8px;
    background: transparent;
    color: inherit;
  }
  .new button {
    padding: 4px 10px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    font-size: var(--text-caption);
  }
  li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 8px;
    border-radius: 12px;
  }
  li:hover {
    background-color: var(--color-gray-50);
  }
  :global([data-theme='dark']) li:hover {
    background-color: var(--color-gray-900);
  }
  li button {
    display: grid;
    color: var(--color-gray-400);
  }
  .none {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .typed {
    inline-size: 100%;
    margin-block-start: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    font-size: var(--text-ui);
  }
</style>
