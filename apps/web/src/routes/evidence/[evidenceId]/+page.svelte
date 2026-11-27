<script lang="ts">
  // Evidence review (web-screens.md, /evidence/[evidenceId]; WP-UI-07, part 1): what the Reader
  // read from a piece of evidence, checked against the page itself.
  import { m } from '$lib/i18n/generated/messages.js';
  import EgressIndicator from '$lib/ui/components/EgressIndicator.svelte';
  import EvidenceViewer from '$lib/ui/components/EvidenceViewer.svelte';
  import TopBar from '$lib/ui/components/TopBar.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();
</script>

<svelte:head><title>{`${data.evidence.name} / ${m.app_name()}`}</title></svelte:head>

<div class="evidence">
  <TopBar title={data.evidence.name}>
    {#snippet end()}
      <EgressIndicator />
    {/snippet}
  </TopBar>
  <div class="page">
    <h1 class="sr-only">Evidence: {data.evidence.name}</h1>
    <p class="meta">Read as {data.evidence.kind} by <code>{data.evidence.reader}</code></p>
    {#key data.evidence.id}
      <EvidenceViewer evidence={data.evidence} box={data.box} />
    {/key}
  </div>
</div>

<style>
  .evidence {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
  }

  .page {
    inline-size: 100%;
    max-inline-size: 1040px;
    margin-inline: auto;
    padding: var(--spacing-6) var(--spacing-4) var(--spacing-12);
  }

  .meta {
    margin-block-end: var(--spacing-4);
    color: var(--color-ink-3);
    font-size: var(--text-small);
  }
</style>
