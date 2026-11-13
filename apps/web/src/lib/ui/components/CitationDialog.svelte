<script lang="ts">
  // The citation dialog (chat-messages look §7.3): the source's name as the title, then the cited
  // passage under its caption. Opened from an evidence chip or a sources-list row.
  import type { Source } from '$lib/data';
  import Dialog from './Dialog.svelte';

  type Props = { source?: Source; open?: boolean };

  let { source, open = $bindable(false) }: Props = $props();
</script>

<Dialog bind:open title={source?.title ?? 'Citation'} closeLabel="Close citation modal" size="wide">
  {#if source}
    <div class="document">
      <p class="caption">Passage</p>
      <p class="passage">{source.passage || 'No passage.'}</p>
    </div>
  {/if}
</Dialog>

<style>
  .document {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
    max-block-size: 352px;
    overflow-y: auto;
    scrollbar-width: thin;
  }

  .caption {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  :global([data-theme='dark']) .caption {
    color: var(--color-gray-400);
  }

  .passage {
    color: var(--color-ink-1);
    font-size: var(--text-ui);
    line-height: 1.625;
    white-space: pre-wrap;
  }
</style>
