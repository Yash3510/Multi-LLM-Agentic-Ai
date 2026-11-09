<script lang="ts">
  // New model (F32): the editor, then back to the list once saved. New knowledge base (F56): the
  // list with the create dialog open; closing it goes to the plain list.
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { data as source } from '$lib/data';
  import { m } from '$lib/i18n/generated/messages.js';
  import CreateKnowledgeDialog from '$lib/ui/components/CreateKnowledgeDialog.svelte';
  import KnowledgeList from '$lib/ui/components/KnowledgeList.svelte';
  import ModelEditor from '$lib/ui/components/ModelEditor.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  const back = (tab: 'models' | 'knowledge') =>
    goto(resolve(`/workspace/${tab}`), { invalidateAll: true });
</script>

<svelte:head
  ><title>{data.tab === 'models' ? 'Models' : 'Knowledge'} / {m.app_name()}</title></svelte:head
>

{#if data.tab === 'models'}
  <ModelEditor
    {...data.editor}
    onsave={async (record) => {
      await source.saveModel(record);
      await back('models');
    }}
  />
{:else}
  <KnowledgeList bases={data.bases} me={data.user?.email} admin={data.user?.role === 'admin'} />
  <CreateKnowledgeDialog
    open
    onclose={() => back('knowledge')}
    oncreate={async (name, description) => {
      await source.createKnowledge(name, description);
      await back('knowledge');
    }}
  />
{/if}
