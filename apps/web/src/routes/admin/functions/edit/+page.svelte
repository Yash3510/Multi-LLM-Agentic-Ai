<script lang="ts">
  // An existing function (admin look §16): shown read only until the 4CE server saves functions.
  import FunctionEditor from '$lib/ui/components/FunctionEditor.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

{#key data.fn.id}<FunctionEditor fn={data.fn} />{/key}
