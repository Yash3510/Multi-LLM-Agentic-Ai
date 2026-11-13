<script lang="ts">
  // Usage (chat-composer look §9.12, F101): the overview, the token activity heat map (daily,
  // weekly or running totals, coloured by each day's top model), insights, top models and tools.
  import type { DataSource, Usage } from '$lib/data';
  import {
    compact,
    duration,
    heatCells,
    heatColours,
    intensity,
    monthLabels,
    paletteFor,
    showHeat,
    topModel,
    type HeatMode,
  } from '$lib/ui/usage';
  import './settings-page.css';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  let usage = $state<Usage>();
  let failed = $state(false);
  let names = $state(new Map<string, string>());
  let mode = $state<HeatMode>('daily');
  let width = $state(0);

  async function load() {
    try {
      usage = await source.getUsage();
    } catch {
      failed = true;
    }
    const models = await source.listBaseModels();
    names = new Map(models.map((one) => [one.id, one.name]));
  }
  void load();

  const MODES: [HeatMode, string][] = [
    ['daily', 'Daily'],
    ['weekly', 'Weekly'],
    ['cumulative', 'Cumulative'],
  ];
  // Cells are 8 to 10 px with 4 px gaps; at least 26 weeks show.
  const days = $derived(usage ? showHeat(usage.daily, mode, usage.weekly, usage.cumulative) : []);
  const total = $derived(Math.max(Math.ceil(days.length / 7), 1));
  const fits = $derived(
    width ? Math.max(Math.min(total, 26), Math.floor((width + 4) / 12)) : Math.min(total, 26),
  );
  const cells = $derived(heatCells(days, Math.min(total, fits)));
  const columns = $derived(Math.max(Math.ceil(cells.length / 7), 1));
  const gridWidth = $derived(`min(100%, ${columns * 10 + (columns - 1) * 4}px)`);
  const months = $derived(monthLabels(cells, columns));
  // Optional because jsdom, which component tests run in, has no ResizeObserver.
  function measure(node: HTMLElement) {
    width = node.clientWidth;
    const observer = globalThis.ResizeObserver
      ? new ResizeObserver(() => (width = node.clientWidth))
      : undefined;
    observer?.observe(node);
    return () => observer?.disconnect();
  }
  const name = (id: string) => names.get(id) ?? id;

  function tip(day: Usage['daily'][number]) {
    const when =
      mode === 'weekly'
        ? `Week of ${day.date}`
        : mode === 'cumulative'
          ? `Through ${day.date}`
          : day.date;
    const models = Object.entries(day.models)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([id, count]) => `${name(id)} ${count}`)
      .join(', ');
    return `${when}: ${compact(day.tokens)} tokens, ${day.messages} messages, ${day.chats} chats; ${models || 'No model data'}`;
  }
</script>

{#snippet stat(value: string, label: string)}
  <div>
    <div class="value">{value}</div>
    <div class="caption">{label}</div>
  </div>
{/snippet}

<div class="settings-page">
  <h2>Usage</h2>
  {#if failed}
    <p class="failed">Failed to load usage</p>
  {:else if usage}
    <div class="body">
      <section>
        <h3>Overview</h3>
        <div class="overview">
          {@render stat(compact(usage.totals.lifetimeTokens), 'Lifetime tokens')}
          {@render stat(compact(usage.totals.peakDailyTokens), 'Peak tokens')}
          {@render stat(duration(usage.totals.longestChatSeconds), 'Longest active chat')}
          {@render stat(String(usage.totals.currentStreak), 'Current streak')}
          {@render stat(String(usage.totals.longestStreak), 'Longest streak')}
        </div>
      </section>
      <section class="activity">
        <div class="activity-head">
          <h4>Token activity</h4>
          <div class="modes">
            {#each MODES as [value, label] (value)}
              <button type="button" aria-pressed={mode === value} onclick={() => (mode = value)}
                >{label}</button
              >
            {/each}
          </div>
        </div>
        <div class="heat" {@attach measure}>
          <div
            class="grid"
            style:width={gridWidth}
            style:aspect-ratio="{columns} / 7"
            style:grid-template-columns="repeat({columns}, minmax(0, 1fr))"
          >
            {#each cells as cell, index (index)}
              {#if cell}
                {@const fill = heatColours(paletteFor(topModel(cell)), intensity(cell))}
                <div
                  class="cell"
                  title={tip(cell)}
                  aria-label={tip(cell)}
                  style:--light={fill.light}
                  style:--dark={fill.dark}
                ></div>
              {:else}
                <div></div>
              {/if}
            {/each}
          </div>
          <div
            class="months"
            style:width={gridWidth}
            style:grid-template-columns="repeat({columns}, minmax(0, 1fr))"
          >
            {#each months as month (month.column)}
              <div style:grid-column="{month.column} / span {month.span}">{month.label}</div>
            {/each}
          </div>
        </div>
        {#if usage.topModels.length}
          <div class="legend">
            {#each usage.topModels.slice(0, 6) as model (model.id)}
              {@const fill = heatColours(paletteFor(model.id), 3)}
              <span class="key">
                <span class="swatch" style:--light={fill.light} style:--dark={fill.dark}></span>
                <span class="key-name">{name(model.id)}</span>
              </span>
            {/each}
          </div>
        {/if}
      </section>
      {#if usage.totals.messages || usage.totals.lifetimeTokens}
        <section>
          <h3>Activity insights</h3>
          <div class="rows">
            {#each [['Models', String(usage.totals.modelsUsed)], ['Average tokens per chat', compact(usage.insights.averageTokensPerChat)], ['Average messages per active day', String(usage.insights.averageMessagesPerActiveDay)], ['User messages', `${usage.totals.userMessages} · ${usage.insights.userMessageShare}%`], ['Assistant messages', `${usage.totals.assistantMessages} · ${usage.insights.assistantMessageShare}%`], ['Total chats', String(usage.totals.totalChats)]] as [label, value] (label)}
              <div class="row">
                <span>{label}</span><span class="strut"><span class="figure">{value}</span></span>
              </div>
            {/each}
          </div>
        </section>
        <section>
          <h3>Top models</h3>
          <div class="rows">
            {#each usage.topModels as model (model.id)}
              <div class="row">
                <span>{name(model.id)}</span>
                <span class="strut"
                  ><span class="count">{model.messages} messages · {compact(model.tokens)}</span
                  ></span
                >
              </div>
            {:else}
              <p class="none">No model usage found</p>
            {/each}
          </div>
        </section>
        {#if usage.topTools.length}
          <section>
            <h3>Most used tools</h3>
            <div class="rows">
              {#each usage.topTools as tool (tool.name)}
                <div class="row">
                  <span>{tool.name}</span><span class="strut"
                    ><span class="count">{tool.count} runs</span></span
                  >
                </div>
              {/each}
            </div>
          </section>
        {/if}
      {:else}
        <section>
          <h3>Activity</h3>
          <p class="none">No usage data found</p>
        </section>
      {/if}
      <p class="footnote">Token counts are estimates and may not reflect actual API usage</p>
    </div>
  {/if}
</div>

<style>
  .failed {
    margin: auto;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .overview {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px 24px;
  }

  @media (min-width: 48rem) {
    .overview {
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }
  }

  .value {
    color: var(--color-gray-900);
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
    line-height: 20px;
  }

  .caption,
  h4,
  .months,
  .legend,
  .footnote {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) :is(.caption, h4, .months, .legend, .footnote) {
    color: var(--color-gray-600);
  }

  .caption {
    margin-block-start: 2px;
    font-size: 11px;
    line-height: 16px;
  }

  :global([data-theme='dark']) .value,
  :global([data-theme='dark']) .figure {
    color: var(--color-white);
  }

  .settings-page section.activity {
    margin-block-start: 16px;
  }

  .activity-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-block-end: 9px;
  }

  h4 {
    min-inline-size: 0;
    overflow: hidden;
    font-size: var(--text-caption);
    font-weight: 400;
    line-height: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .modes {
    display: flex;
    gap: 12px;
    max-inline-size: 70%;
    overflow: hidden;
    white-space: nowrap;
  }

  .modes button {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
    transition: color 150ms;
  }

  .modes button:hover {
    color: var(--color-gray-700);
  }

  .modes button[aria-pressed='true'] {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .modes button:hover {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .modes button[aria-pressed='true'] {
    color: var(--color-white);
  }

  .heat {
    inline-size: 100%;
    min-inline-size: 0;
    padding-block-end: 4px;
    overflow: hidden;
  }

  .grid {
    display: grid;
    grid-auto-flow: column;
    grid-template-rows: repeat(7, minmax(0, 1fr));
    gap: 4px;
    margin-inline: auto;
  }

  .cell,
  .swatch {
    border-radius: 2px;
    background-color: var(--light);
  }

  :global([data-theme='dark']) :is(.cell, .swatch) {
    background-color: var(--dark);
  }

  .months {
    display: grid;
    column-gap: 4px;
    margin: 8px auto 0;
    font-size: 11px;
    line-height: 1;
  }

  .months div {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 12px;
    /* Measured against the running app. */
    margin-block-start: 1px;
    padding-block-end: 3px;
    font-size: 11px;
  }

  .key {
    display: flex;
    align-items: center;
    gap: 6px;
    min-inline-size: 0;
  }

  .swatch {
    flex-shrink: 0;
    inline-size: 8px;
    block-size: 8px;
  }

  .key-name {
    max-inline-size: 112px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* As the running app: the 12 px value sits in a 14 px line, so each row is 24 px tall and the
     value 2 px lower than the label. */
  .strut {
    display: block;
    block-size: 24px;
    padding-block-start: 4px;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  .figure,
  .count {
    font-size: var(--text-caption);
  }

  .figure {
    color: var(--color-gray-900);
  }

  .count {
    color: var(--color-gray-500);
  }

  :global([data-theme='dark']) .count {
    color: var(--color-gray-400);
  }

  .none {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .none {
    color: var(--color-gray-400);
  }

  .footnote {
    margin-block-start: 16px;
    font-size: 11px;
    text-align: end;
  }
</style>
