<script lang="ts">
  // A channel (channels look §3).
  import { data as source } from '$lib/data';
  import ChannelView from '$lib/ui/components/ChannelView.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

<svelte:head><title># {data.channel.name} / 4CE</title></svelte:head>

{#key data.channel.id}
  <ChannelView {source} channel={data.channel} selfId={data.user?.id ?? ''} />
{/key}
