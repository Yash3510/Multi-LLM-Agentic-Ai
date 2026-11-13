<script lang="ts">
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { data as source } from '$lib/data';
  import AutomationEditor from '$lib/ui/components/AutomationEditor.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

{#key data.automation.id}
  <AutomationEditor
    {source}
    automation={data.automation}
    onsaved={() => goto(resolve('/automations'))}
  />
{/key}
