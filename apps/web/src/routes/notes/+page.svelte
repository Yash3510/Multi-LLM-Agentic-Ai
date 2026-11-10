<script lang="ts">
  // Notes (notes look §1).
  import { page } from '$app/state';
  import { data as source } from '$lib/data';
  import NoteList from '$lib/ui/components/NoteList.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

<svelte:head><title>Notes / 4CE</title></svelte:head>

<NoteList
  {source}
  selfEmail={data.user?.email}
  deletedId={page.url.searchParams.get('deleted') ?? undefined}
/>
