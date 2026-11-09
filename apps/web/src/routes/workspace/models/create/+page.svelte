<script lang="ts">
  // New model (workspace F32): the editor, then back to the list once it is saved.
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { data as source } from '$lib/data';
  import { m } from '$lib/i18n/generated/messages.js';
  import ModelEditor from '$lib/ui/components/ModelEditor.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

<svelte:head><title>Models / {m.app_name()}</title></svelte:head>

<ModelEditor
  {...data}
  onsave={async (record) => {
    await source.saveModel(record);
    await goto(resolve('/workspace/models'), { invalidateAll: true });
  }}
/>
