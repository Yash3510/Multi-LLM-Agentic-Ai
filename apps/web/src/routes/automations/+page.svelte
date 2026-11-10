<script lang="ts">
  import { data as source } from '$lib/data';
  import AutomationList from '$lib/ui/components/AutomationList.svelte';
</script>

<svelte:head><title>Automations / 4CE</title></svelte:head>

<AutomationList {source} />
