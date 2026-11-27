<script lang="ts">
  // The evidence viewer (web-screens.md): the page image with numbered observation boxes, and the
  // observation list in step with them. Selecting a box selects its row and the reverse; what was
  // read with less than full confidence is drawn dashed and asks for a check. The list follows the
  // page shown. Zoomed in, the frame scrolls, so panning is the browser's own: wheel, trackpad,
  // touch and scrollbars, and the arrow keys once a box has focus.
  import { tick, untrack } from 'svelte';
  import type { Evidence, Observation } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import IconButton from './IconButton.svelte';

  type Props = {
    evidence: Evidence;
    /** The page to open, from 1 (the address's `?page=`). */
    page?: number;
    /** The observation number to open with selected, on its page (the address's `?box=`). */
    box?: number;
  };

  let { evidence, page: asked, box }: Props = $props();

  const opened = untrack(() => evidence.observations.find((one) => one.index === box));
  // A page outside the evidence opens the first.
  let current = $state(
    untrack(() => {
      const first = opened?.page ?? asked ?? 1;
      return evidence.pages[first - 1] ? first : 1;
    }),
  );
  let selected = $state(opened?.id);

  const page = $derived(evidence.pages[current - 1]);
  const observations = $derived(evidence.observations.filter((one) => one.page === current));

  // From the page fitting its frame to four times that.
  const ZOOMS = [1, 1.5, 2, 3, 4];
  let zoom = $state(1);
  let frame: HTMLDivElement | undefined = $state();

  // The point at the frame's centre stays there.
  async function zoomBy(step: number) {
    const next = ZOOMS[ZOOMS.indexOf(zoom) + step];
    if (!next || !frame) return;
    const { scrollLeft, scrollTop, scrollWidth, scrollHeight, clientWidth, clientHeight } = frame;
    zoom = next;
    await tick();
    frame.scrollLeft =
      ((scrollLeft + clientWidth / 2) / scrollWidth) * frame.scrollWidth - clientWidth / 2;
    frame.scrollTop =
      ((scrollTop + clientHeight / 2) / scrollHeight) * frame.scrollHeight - clientHeight / 2;
  }

  const percent = (fraction: number) => `${(fraction * 100).toFixed(2)}%`;
  const reading = (one: Observation) => [one.value, one.unit].filter(Boolean).join(' ');
</script>

<div class="viewer">
  <div class="pane">
    {#if page}
      <div class="tools">
        {#if evidence.pages.length > 1}
          <IconButton
            icon="caret-left"
            label="Previous page"
            disabled={current === 1}
            onclick={() => (current -= 1)}
          />
          <span class="where" aria-live="polite">Page {current} of {evidence.pages.length}</span>
          <IconButton
            icon="caret-right"
            label="Next page"
            disabled={current === evidence.pages.length}
            onclick={() => (current += 1)}
          />
        {/if}
        <span class="zoom">
          <IconButton
            icon="minus"
            label="Zoom out"
            disabled={zoom === ZOOMS[0]}
            onclick={() => zoomBy(-1)}
          />
          <span class="where" aria-live="polite">Zoom {zoom * 100}%</span>
          <IconButton
            icon="plus"
            label="Zoom in"
            disabled={zoom === ZOOMS.at(-1)}
            onclick={() => zoomBy(1)}
          />
        </span>
      </div>
      <!-- A scrolling region takes focus, so a zoomed page with no boxes still pans by keyboard. -->
      <div
        class="frame"
        bind:this={frame}
        role="region"
        tabindex="0"
        aria-label={`Page ${current} of ${evidence.pages.length}, zoom ${zoom * 100}%`}
        style:aspect-ratio={`${page.width} / ${page.height}`}
      >
        <div
          class="page"
          style:inline-size={`${zoom * 100}%`}
          style:aspect-ratio={`${page.width} / ${page.height}`}
        >
          <img src={page.image} alt={`Page ${current} of ${evidence.name}`} />
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
      </div>
    {/if}
  </div>
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

  .pane {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .tools {
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
  }

  .where {
    color: var(--color-ink-3);
    font-size: var(--text-small);
    font-variant-numeric: tabular-nums;
  }

  .zoom {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    margin-inline-start: auto;
  }

  /* The frame is the page at its fit, and scrolls when zoomed in. Its content box keeps the page's
     aspect ratio, so at 100% nothing scrolls. */
  .frame {
    box-sizing: content-box;
    overflow: auto;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-control);
  }

  /* The page keeps its own aspect ratio, so the boxes sit where they were read. */
  .page {
    position: relative;
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

  .frame:focus-visible,
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
