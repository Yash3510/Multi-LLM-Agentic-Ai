<script lang="ts">
  // The evidence viewer (web-screens.md): the page image with numbered observation boxes, and the
  // observation list in step with them. Selecting a box selects its row and the reverse; what was
  // read with less than full confidence is drawn dashed and asks for a check.
  import { untrack } from 'svelte';
  import type { Evidence, Observation } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    evidence: Evidence;
    /** The observation number to open with selected (the address's `?box=`). */
    box?: number;
  };

  let { evidence, box }: Props = $props();

  const page = $derived(evidence.pages[0]);
  const observations = $derived(evidence.observations.filter((one) => one.page === 1));
  let selected = $state(untrack(() => evidence.observations.find((one) => one.index === box)?.id));

  const percent = (fraction: number) => `${(fraction * 100).toFixed(2)}%`;
  const reading = (one: Observation) => [one.value, one.unit].filter(Boolean).join(' ');
</script>

<div class="viewer">
  {#if page}
    <div class="page" style:aspect-ratio={`${page.width} / ${page.height}`}>
      <img src={page.image} alt={`Page 1 of ${evidence.name}`} />
      {#each observations as one (one.id)}
        <button
          type="button"
          class="box"
          style:left={percent(one.box.x)}
          style:top={percent(one.box.y)}
          style:width={percent(one.box.width)}
          style:height={percent(one.box.height)}
          aria-label={`Box ${one.index}: ${one.label}, ${reading(one)}`}
          aria-pressed={selected === one.id}
          data-unsure={one.confidence < 1 ? '' : undefined}
          onclick={() => (selected = one.id)}><span class="tab">{one.index}</span></button
        >
      {/each}
    </div>
  {/if}
  <ol class="list" aria-label="What was read">
    {#each observations as one (one.id)}
      <li>
        <button
          type="button"
          class="row"
          aria-pressed={selected === one.id}
          onclick={() => (selected = one.id)}
        >
          <span class="number">{one.index}</span>
          <span class="label">{one.label}</span>
          <span class="value">{reading(one)}</span>
          <span class="confidence">{Math.round(one.confidence * 100)}%</span>
          {#if one.confidence < 1}
            <span class="check"><Icon name="observation-unsure" size={14} />check</span>
          {/if}
        </button>
      </li>
    {:else}
      <li class="none">Nothing was read from this page.</li>
    {/each}
  </ol>
</div>

<style>
  .viewer {
    display: grid;
    grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
    gap: var(--spacing-6);
    align-items: start;
  }

  @media (max-width: 47.99rem) {
    .viewer {
      grid-template-columns: minmax(0, 1fr);
    }
  }

  /* The page keeps its own aspect ratio, so the boxes sit where they were read. */
  .page {
    position: relative;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-control);
    overflow: hidden;
  }

  .page img {
    display: block;
    inline-size: 100%;
    block-size: 100%;
  }

  /* A box with a numbered tab at its corner; dashed when unsure (design system, observation). */
  .box {
    position: absolute;
    border: 2px solid var(--color-ink-1);
    border-radius: 3px;
  }

  .box[data-unsure] {
    border-style: dashed;
  }

  .box[aria-pressed='true'] {
    box-shadow: var(--shadow-focus);
  }

  .box:focus-visible,
  .row:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .tab {
    position: absolute;
    inset: -2px auto auto -2px;
    translate: 0 -100%;
    padding-inline: 4px;
    border-radius: 3px 3px 0 0;
    background-color: var(--color-ink-1);
    color: var(--color-surface-raised);
    font-family: var(--font-mono);
    font-size: var(--text-tag);
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .row {
    display: grid;
    grid-template-columns: 24px minmax(0, 1fr) auto auto;
    align-items: baseline;
    gap: var(--spacing-1) var(--spacing-3);
    inline-size: 100%;
    padding: var(--spacing-2) var(--spacing-3);
    border-radius: var(--radius-control);
    font-size: var(--text-small);
    text-align: start;
  }

  .row:hover,
  .row[aria-pressed='true'] {
    background-color: var(--color-tint);
  }

  .number,
  .confidence {
    color: var(--color-ink-3);
    font-family: var(--font-mono);
    font-size: var(--text-tag);
  }

  .value {
    color: var(--color-ink-1);
    font-variant-numeric: tabular-nums;
  }

  .check {
    display: inline-flex;
    grid-column: 2 / -1;
    align-items: center;
    gap: var(--spacing-1);
    color: var(--color-caution);
  }

  .none {
    color: var(--color-ink-3);
    font-size: var(--text-small);
  }
</style>
