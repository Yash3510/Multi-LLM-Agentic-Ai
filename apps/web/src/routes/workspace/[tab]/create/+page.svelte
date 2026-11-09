<script lang="ts">
  // New model (F32): the editor, then back to the list once saved. New knowledge base (F56): the
  // list with the create dialog open; closing it goes to the plain list.
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { data as source } from '$lib/data';
  import { m } from '$lib/i18n/generated/messages.js';
  import CreateKnowledgeDialog from '$lib/ui/components/CreateKnowledgeDialog.svelte';
  import CreatePromptDialog from '$lib/ui/components/CreatePromptDialog.svelte';
  import KnowledgeList from '$lib/ui/components/KnowledgeList.svelte';
  import ModelEditor from '$lib/ui/components/ModelEditor.svelte';
  import PromptList from '$lib/ui/components/PromptList.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  const back = (tab: 'models' | 'knowledge' | 'prompts') =>
    goto(resolve(`/workspace/${tab}`), { invalidateAll: true });
</script>

<svelte:head
  ><title
    >{{ models: 'Models', knowledge: 'Knowledge', prompts: 'Prompts' }[data.tab]} / {m.app_name()}</title
  ></svelte:head
>

{#if data.tab === 'models'}
  <ModelEditor
    {...data.editor}
    onsave={async (record) => {
      await source.saveModel(record);
      await back('models');
    }}
  />
{:else if data.tab === 'prompts'}
  <PromptList prompts={data.prompts} me={data.user?.email} />
  <CreatePromptDialog
    open
    onclose={() => back('prompts')}
    oncreate={async (draft) => {
      await source.createPrompt(draft);
      await back('prompts');
    }}
  />
{:else}
  <KnowledgeList
    bases={data.bases}
    me={data.user?.email}
    admin={data.user?.role === 'admin'}
    onopen={(id) => goto(resolve('/workspace/[tab]/[id]', { tab: 'knowledge', id }))}
  />
  <CreateKnowledgeDialog
    open
    onclose={() => back('knowledge')}
    oncreate={async (name, description) => {
      const made = await source.createKnowledge(name, description);
      await goto(resolve('/workspace/[tab]/[id]', { tab: 'knowledge', id: made.id }));
    }}
  />
{/if}
