<script lang="ts">
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { data as source } from '$lib/data';
  import AutomationEditor from '$lib/ui/components/AutomationEditor.svelte';
</script>

<AutomationEditor {source} onsaved={() => goto(resolve('/automations'))} />
