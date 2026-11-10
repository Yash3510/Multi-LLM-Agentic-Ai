<script lang="ts">
  // The calendar (calendar look §1).
  import { data as source } from '$lib/data';
  import CalendarView from '$lib/ui/components/CalendarView.svelte';
</script>

<svelte:head><title>Calendar / 4CE</title></svelte:head>

<CalendarView {source} />
