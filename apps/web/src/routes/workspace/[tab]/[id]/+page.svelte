<script lang="ts">
  import { data as source } from '$lib/data';
  import { m } from '$lib/i18n/generated/messages.js';
  import KnowledgeDetail from '$lib/ui/components/KnowledgeDetail.svelte';
  import PromptPage from '$lib/ui/components/PromptPage.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

<svelte:head
  ><title>{data.tab === 'knowledge' ? data.base.name : data.prompt.name} / {m.app_name()}</title
  ></svelte:head
>

{#if data.tab === 'knowledge'}
  {#key data.base.id}<KnowledgeDetail base={data.base} {source} />{/key}
{:else}
  {#key data.prompt.id}<PromptPage prompt={data.prompt} {source} />{/key}
{/if}
