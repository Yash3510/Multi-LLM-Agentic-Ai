<script lang="ts">
  // The sign-off page (web-screens.md, /runs/[runId]/sign-off): the run view itself, with the
  // sign-off panel docked, so both addresses show one run.
  import RunView from '../+page.svelte';
  import type { PageProps } from './$types';

  let { data, params }: PageProps = $props();
</script>

<RunView {data} {params} />
