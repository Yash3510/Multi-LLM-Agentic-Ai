<script lang="ts">
  import { data as source } from '$lib/data';
  import { m } from '$lib/i18n/generated/messages.js';
  import KnowledgeDetail from '$lib/ui/components/KnowledgeDetail.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

<svelte:head><title>{data.base.name} / {m.app_name()}</title></svelte:head>

{#key data.base.id}<KnowledgeDetail base={data.base} {source} />{/key}
