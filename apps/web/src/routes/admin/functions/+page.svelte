<script lang="ts">
  // Functions (admin look §15): the list, read only in this build.
  import { data as source } from '$lib/data';
  import FunctionList from '$lib/ui/components/FunctionList.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

<FunctionList {source} selfEmail={data.user?.email} />
