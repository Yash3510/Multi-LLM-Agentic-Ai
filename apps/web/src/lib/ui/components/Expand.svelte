<script lang="ts">
  // A panel that opens smoothly (ADR-0042): mount it when its row opens. The rows grow from 0fr to
  // 1fr at calm, from a starting style, so a closed panel stays out of the page. It closes at once.
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
</script>

<div class="expand"><div class="inner">{@render children()}</div></div>

<style>
  .expand {
    display: grid;
    grid-template-rows: 1fr;
    transition: grid-template-rows var(--duration-calm) var(--ease-expo);
  }

  .inner {
    min-block-size: 0;
    overflow: hidden;
    transition: opacity var(--duration-calm) var(--ease-out);
  }

  @starting-style {
    .expand {
      grid-template-rows: 0fr;
    }

    .inner {
      opacity: 0;
    }
  }
</style>
