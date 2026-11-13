<script lang="ts">
  // A model's details (admin look §13c, F109 to F113): its wins and losses over 30 days, a year
  // or all time as diverging bars (wins up, losses down; weeks for the longer ranges), and its
  // most used tags. The bars are plain SVG, so no chart library is needed.
  import { Dialog } from 'bits-ui';
  import type { DataSource } from '$lib/data';
  import { type ActivityDay, type BoardRow, weekly } from '$lib/ui/evaluations';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './admin-dialog.css';
  import './modal.css';

  type Props = { open: boolean; source: DataSource; model?: BoardRow; onclose: () => void };

  let { open, source, model, onclose }: Props = $props();

  const RANGES: [number, string][] = [
    [30, '30D'],
    [365, '1Y'],
    [0, 'All'],
  ];
  let range = $state(30);
  let days = $state<ActivityDay[]>();

  // Each opening starts on 30 days.
  $effect(() => {
    if (open) range = 30;
  });

  $effect(() => {
    if (!open || !model) return;
    const chosen = range;
    days = undefined;
    void source.modelActivity(model.id, chosen).then((loaded) => {
      days = chosen !== 30 && loaded.length > 7 ? weekly(loaded) : loaded;
    });
  });

  const active = $derived((days ?? []).some((day) => day.won || day.lost));
  const peak = $derived(Math.max(1, ...(days ?? []).flatMap((day) => [day.won, day.lost])));
  const label = (date: string) =>
    new Date(`${date}T00:00:00Z`).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      timeZone: 'UTC',
    });
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog medium">
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}
              <h3 {...props} class="title clamp" title="{model?.name} ({model?.id})">
                {model?.name}
              </h3>
            {/snippet}
          </Dialog.Title>
          <Dialog.Close class="close" aria-label="Close"><Icon name="x" size={16} /></Dialog.Close>
        </div>
        <div class="body">
          <section>
            <div class="row">
              <h4>Activity</h4>
              <div class="ranges" role="group" aria-label="Range">
                {#each RANGES as [value, text] (value)}
                  <button
                    type="button"
                    aria-pressed={range === value}
                    onclick={() => (range = value)}>{text}</button
                  >
                {/each}
              </div>
            </div>
            {#if !days}
              <p class="box" aria-busy="true">Loading…</p>
            {:else if !active}
              <p class="box">No activity data</p>
            {:else}
              <svg
                class="chart"
                viewBox="0 0 {days.length * 10} 192"
                preserveAspectRatio="none"
                role="img"
                aria-label="Won and lost by day"
              >
                {#each days as day, index (day.date)}
                  <g>
                    <title>{label(day.date)} — Won: {day.won}, Lost: {day.lost}</title>
                    <rect
                      class="won"
                      x={index * 10 + 0.5}
                      y={96 - (day.won / peak) * 88}
                      width="9"
                      height={(day.won / peak) * 88}
                      rx="2"
                    />
                    <rect
                      class="lost"
                      x={index * 10 + 0.5}
                      y="96"
                      width="9"
                      height={(day.lost / peak) * 88}
                      rx="2"
                    />
                  </g>
                {/each}
              </svg>
            {/if}
          </section>
          <section>
            <h4>Tags</h4>
            {#if model?.tags.length}
              <div class="tags">
                {#each model.tags as { tag, count } (tag)}
                  <span class="tag">{tag} <span class="count">{count}</span></span>
                {/each}
              </div>
            {:else}
              <p class="dash">-</p>
            {/if}
          </section>
          <div class="footer">
            <button type="button" class="pill" onclick={onclose}>Close</button>
          </div>
        </div>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .clamp {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .body {
    padding: 0 20px 16px;
  }

  section {
    margin-block-end: 16px;
  }

  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: 8px;
  }

  h4 {
    margin-block-end: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    font-weight: 400;
    letter-spacing: 0.025em;
    text-transform: uppercase;
  }

  .row h4 {
    margin: 0;
  }

  .ranges {
    display: flex;
    padding: 2px;
    border-radius: var(--radius-pill);
    background-color: color-mix(in srgb, var(--color-gray-100) 80%, transparent);
    backdrop-filter: blur(24px);
  }

  :global([data-theme='dark']) .ranges {
    background-color: color-mix(in srgb, var(--color-gray-800) 80%, transparent);
  }

  .ranges button {
    padding: 2px 10px;
    border-radius: var(--radius-pill);
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    transition: all 200ms;
  }

  .ranges button:hover {
    color: var(--color-gray-700);
  }

  .ranges button[aria-pressed='true'] {
    background-color: var(--color-white);
    box-shadow:
      0 1px 3px 0 rgb(0 0 0 / 0.1),
      0 1px 2px -1px rgb(0 0 0 / 0.1);
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .ranges button {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .ranges button[aria-pressed='true'] {
    background-color: var(--color-gray-700);
    color: var(--color-white);
  }

  .box {
    display: grid;
    place-items: center;
    block-size: 160px;
    color: var(--color-gray-500);
    font-size: var(--text-ui);
  }

  .chart {
    display: block;
    inline-size: 100%;
    block-size: 192px;
  }

  .chart .won {
    fill: var(--color-chart-won);
  }

  .chart .lost {
    fill: var(--color-chart-lost);
  }

  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-inline: -4px;
  }

  .tag {
    padding: 2px 8px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-100);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .tag {
    background-color: var(--color-gray-850);
  }

  .count {
    color: var(--color-gray-500);
  }

  .dash {
    color: var(--color-gray-500);
    font-size: var(--text-ui);
  }

  .footer {
    padding-block-start: 8px;
  }

  .ranges button:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
