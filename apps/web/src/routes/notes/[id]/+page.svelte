<script lang="ts">
  // A note (notes look §2). Deleting returns to the list, which offers Undo.
  import { goto } from '$app/navigation';
  import { appHref } from '$lib/ui/app-href';
  import { data as source } from '$lib/data';
  import NoteEditor from '$lib/ui/components/NoteEditor.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

<svelte:head><title>{data.note.title || 'Untitled'} / 4CE</title></svelte:head>

{#key data.note.id}
  <NoteEditor
    {source}
    note={data.note}
    ondeleted={() => goto(appHref(`/notes?deleted=${data.note.id}`))}
  />
{/key}
