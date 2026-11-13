<script lang="ts">
  // The leaderboard (admin look §13b, F95 to F108): every model with its Elo rating, wins and
  // losses (shares on hover), sortable and searchable; a row opens the model's details.
  import type { DataSource } from '$lib/data';
  import {
    type BoardColumn,
    type BoardRow,
    leaderboardRows,
    share,
    sortRows,
  } from '$lib/ui/evaluations';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Logomark from './Logomark.svelte';
  import ModelDetailsDialog from './ModelDetailsDialog.svelte';
  import './admin-table.css';

  type Props = { source: DataSource; oncount?: (count: number) => void };

  let { source, oncount }: Props = $props();

  let rows = $state<BoardRow[]>();
  let query = $state('');
  let sort = $state<{ column: BoardColumn; ascending: boolean }>({
    column: 'rating',
    ascending: false,
  });
  let hovered = $state<string>();
  let open = $state<BoardRow>();

  async function load() {
    const [models, entries] = await Promise.all([source.listBaseModels(), source.leaderboard()]);
    rows = leaderboardRows(models, entries);
    oncount?.(rows.length);
  }
  void load();

  const shown = $derived(
    sortRows(
      (rows ?? []).filter((row) =>
        `${row.name} ${row.id}`.toLowerCase().includes(query.trim().toLowerCase()),
      ),
      sort,
    ),
  );

  const COLUMNS: [BoardColumn, string, string, boolean][] = [
    ['rating', 'RK', 'rank', false],
    ['name', 'Model', 'model', false],
    ['rating', 'Rating', 'rating', true],
    ['won', 'Won', 'won', true],
    ['lost', 'Lost', 'lost', true],
  ];

  const sortBy = (column: BoardColumn) =>
    (sort =
      sort.column === column
        ? { column, ascending: !sort.ascending }
        : { column, ascending: column === 'name' });

  const ariaSort = (column: BoardColumn) =>
    sort.column === column ? (sort.ascending ? 'ascending' : 'descending') : 'none';

  function count(row: BoardRow, value: number | undefined) {
    const total = (row.won ?? 0) + (row.lost ?? 0);
    if (value === undefined || !total) return '-';
    return hovered === row.id ? share(value, total) : String(value);
  }
</script>

<div class="admin-table">
  <div class="toolbar">
    <label class="search">
      <Icon name="magnifying-glass" size={14} />
      <input bind:value={query} placeholder="Search" aria-label="Search" />
      {#if query}
        <button type="button" class="clear" aria-label="Clear search" onclick={() => (query = '')}
          ><Icon name="x-bold" size={12} /></button
        >
      {/if}
    </label>
  </div>
  {#if rows && !shown.length}
    <p class="empty">No models found</p>
  {:else if rows}
    <div class="scroller">
      <table>
        <thead>
          <tr>
            {#each COLUMNS as [column, label, key, end] (key)}
              <th class={key} class:end aria-sort={ariaSort(column)}>
                <button type="button" onclick={() => sortBy(column)}>
                  {label}
                  <span class="caret" class:hidden={sort.column !== column} aria-hidden="true">
                    <Icon name={sort.ascending ? 'caret-up' : 'caret-down'} size={8} />
                  </span>
                </button>
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each shown as row (row.id)}
            <tr
              onmouseenter={() => (hovered = row.id)}
              onmouseleave={() => (hovered = undefined)}
              onclick={() => (open = row)}
            >
              <td class="rank">{row.rank ?? '-'}</td>
              <td>
                <span class="model" title="{row.name} ({row.id})">
                  <Logomark size={20} /><span class="name">{row.name}</span>
                </span>
              </td>
              <td class="rating">{row.rating ?? '-'}</td>
              <td class="won">{count(row, row.won)}</td>
              <td class="lost">{count(row, row.lost)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="hint">
      <Icon name="info" size={12} /> The evaluation leaderboard is based on the Elo rating system and
      is updated in real-time.
    </p>
  {/if}
</div>

<ModelDetailsDialog
  open={open !== undefined}
  {source}
  model={open}
  onclose={() => (open = undefined)}
/>

<style>
  .empty {
    padding-block: 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  th.rank {
    inline-size: 12px;
  }

  th.rating {
    inline-size: 1%;
  }

  th.won,
  th.lost {
    inline-size: 20px;
  }

  td {
    padding: 6px 12px;
  }

  .rank,
  .rating {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) :is(.rank, .rating) {
    color: var(--color-white);
  }

  td.rank {
    color: var(--color-gray-900);
  }

  .model {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .model :global(img) {
    border-radius: var(--radius-pill);
  }

  .name {
    overflow: hidden;
    color: var(--color-gray-800);
    text-overflow: ellipsis;
  }

  :global([data-theme='dark']) .name {
    color: var(--color-gray-200);
  }

  .rating,
  .won,
  .lost {
    text-align: end;
  }

  .won {
    inline-size: 40px;
    color: var(--color-green-500);
  }

  .lost {
    inline-size: 40px;
    color: var(--color-red-500);
  }
</style>
