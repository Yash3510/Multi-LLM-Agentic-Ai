<script lang="ts">
  // Feedback history (admin look §14, F114 to F128): filter by model, export as JSON or CSV, a
  // sortable table of ratings, details on click, and delete (confirmed, with Undo, logged).
  import { DropdownMenu } from 'bits-ui';
  import type { DataSource, Feedback } from '$lib/data';
  import { ago } from '$lib/ui/ago';
  import { feedbackCsv } from '$lib/ui/evaluations';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import FeedbackDialog from './FeedbackDialog.svelte';
  import './admin-table.css';
  import './menu.css';
  import './surfaces.css';

  type Props = { source: DataSource; oncount?: (count: number) => void };

  let { source, oncount }: Props = $props();

  type Column = 'user' | 'model' | 'result' | 'updated';
  let records = $state<Feedback[]>();
  let model = $state('');
  let sort = $state<{ column: Column; ascending: boolean }>({
    column: 'updated',
    ascending: false,
  });
  let open = $state<Feedback>();
  let deleting = $state<Feedback>();
  let undo = $state<Feedback>();

  async function load() {
    records = await source.listFeedback();
    oncount?.(records.length);
  }
  void load();

  const models = $derived([...new Set((records ?? []).map((one) => one.modelId))].sort());
  const shown = $derived.by(() => {
    const sign = sort.ascending ? 1 : -1;
    const key = (one: Feedback) =>
      ({
        user: one.userName,
        model: one.modelId,
        result: one.result,
        updated: one.updated.getTime(),
      })[sort.column];
    return (records ?? [])
      .filter((one) => !model || one.modelId === model)
      .sort((a, b) => {
        const [x, y] = [key(a), key(b)];
        return (
          sign *
          (typeof x === 'number' && typeof y === 'number'
            ? x - y
            : String(x).localeCompare(String(y)))
        );
      });
  });

  const COLUMNS: [Column, string, boolean][] = [
    ['user', 'User', false],
    ['model', 'Models', false],
    ['result', 'Result', true],
    ['updated', 'Updated At', true],
  ];
  const RESULTS = { 1: ['Won', 'info'], 0: ['Draw', 'muted'], [-1]: ['Lost', 'error'] } as const;

  const sortBy = (column: Column) =>
    (sort =
      sort.column === column
        ? { column, ascending: !sort.ascending }
        : { column, ascending: true });

  function download(text: string, extension: string, type: string) {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([text], { type }));
    link.download = `feedback-history-export-${Date.now()}.${extension}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  const chosen = () => (records ?? []).filter((one) => !model || one.modelId === model);
  const exportJson = () => download(JSON.stringify(chosen()), 'json', 'application/json');
  const exportCsv = () =>
    download(
      feedbackCsv(
        chosen().map((one) => ({
          ...one,
          created: Math.floor(one.created.getTime() / 1000),
          updated: Math.floor(one.updated.getTime() / 1000),
        })),
      ),
      'csv',
      'text/csv',
    );

  async function remove() {
    if (!deleting) return;
    const gone = deleting;
    deleting = undefined;
    await source.deleteFeedback(gone.id);
    undo = gone;
    await load();
  }

  async function restore() {
    if (!undo) return;
    await source.restoreFeedback(undo.id);
    undo = undefined;
    await load();
  }
</script>

<div class="admin-table">
  {#if !records}
    <p class="loading" aria-busy="true">Loading…</p>
  {:else}
    {#if records.length}
      <div class="bar">
        <div class="filter">
          <DropdownMenu.Root>
            <DropdownMenu.Trigger class="feedback-filter">
              <span class="clamp">{model || 'All'}</span><Icon name="caret-down-bold" size={14} />
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                class="feedback-menu"
                data-menu
                data-surface="float"
                align="start"
                sideOffset={4}
              >
                {#each ['', ...models] as value (value)}
                  <DropdownMenu.Item data-menu-row onSelect={() => (model = value)}>
                    <span class="grow">{value || 'All'}</span>
                    <span class:hidden={model !== value}><Icon name="check" size={16} /></span>
                  </DropdownMenu.Item>
                {/each}
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger class="feedback-export">
            Export<Icon name="caret-down-bold" size={12} />
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              class="feedback-menu"
              data-menu
              data-surface="float"
              align="end"
              sideOffset={4}
            >
              <DropdownMenu.Item data-menu-row onSelect={exportJson}
                >Export as JSON</DropdownMenu.Item
              >
              <DropdownMenu.Item data-menu-row onSelect={exportCsv}>Export as CSV</DropdownMenu.Item
              >
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    {/if}
    {#if undo}
      <p class="undo" role="status">
        Deleted feedback for {undo.modelId}. <button type="button" onclick={restore}>Undo</button>
      </p>
    {/if}
    {#if !shown.length}
      <div class="empty">
        <p class="empty-title">No feedback found</p>
        <p class="empty-hint">
          Try adjusting your search or filter to find what you are looking for.
        </p>
      </div>
    {:else}
      <div class="scroller">
        <table>
          <thead>
            <tr>
              {#each COLUMNS as [column, label, end] (column)}
                <th
                  class:end
                  aria-sort={sort.column === column
                    ? sort.ascending
                      ? 'ascending'
                      : 'descending'
                    : 'none'}
                >
                  <button type="button" onclick={() => sortBy(column)}>
                    {label}
                    <span class="caret" class:hidden={sort.column !== column} aria-hidden="true">
                      <Icon name={sort.ascending ? 'caret-up' : 'caret-down'} size={8} />
                    </span>
                  </button>
                </th>
              {/each}
              <th><span class="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {#each shown as one (one.id)}
              <tr onclick={() => (open = one)}>
                <td class="user"
                  ><span class="avatar" title={one.userName}><Icon name="user" size={12} /></span
                  ></td
                >
                <td class="models">
                  <span class="clamp model" title={one.modelId}>{one.modelId}</span>
                  {#if one.siblings.length}
                    <span class="clamp siblings" title={one.siblings.join(', ')}>
                      {one.siblings.length > 2
                        ? `${one.siblings.slice(0, 2).join(', ')} and ${one.siblings.length - 2} more`
                        : one.siblings.join(', ')}
                    </span>
                  {/if}
                </td>
                <td class="result">
                  <span class="chip" data-tone={RESULTS[one.result][1]}
                    >{RESULTS[one.result][0]}</span
                  >
                </td>
                <td class="updated">{ago(one.updated)}</td>
                <td class="menu-cell">
                  <DropdownMenu.Root>
                    <DropdownMenu.Trigger
                      class="feedback-more"
                      aria-label="More"
                      title="More"
                      onclick={(event) => event.stopPropagation()}
                    >
                      <Icon name="dots-three" size={16} />
                    </DropdownMenu.Trigger>
                    <DropdownMenu.Portal>
                      <DropdownMenu.Content
                        class="feedback-menu narrow"
                        data-menu
                        data-surface="float"
                        align="end"
                        sideOffset={4}
                      >
                        <DropdownMenu.Item data-menu-row onSelect={() => (deleting = one)}>
                          <span data-menu-lead><Icon name="trash" size={14} /></span>Delete
                        </DropdownMenu.Item>
                      </DropdownMenu.Content>
                    </DropdownMenu.Portal>
                  </DropdownMenu.Root>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {/if}
</div>

<FeedbackDialog open={open !== undefined} feedback={open} onclose={() => (open = undefined)} />

<ConfirmDialog
  open={deleting !== undefined}
  title="Delete feedback?"
  message="This removes the rating from the leaderboard. You can undo it straight after."
  confirmLabel="Delete"
  onconfirm={remove}
  oncancel={() => (deleting = undefined)}
/>

<style>
  .loading {
    margin-block: 40px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  .bar {
    display: flex;
    align-items: center;
    gap: 8px;
    block-size: 32px;
  }

  .filter {
    flex: 1;
    min-inline-size: 0;
    overflow-x: auto;
    scrollbar-width: none;
  }

  :global(.feedback-filter) {
    display: flex;
    align-items: center;
    gap: 2px;
    padding: 6px 10px;
    border-radius: 12px;
    color: var(--color-gray-700);
    font-size: 13px;
    transition: color 150ms;
  }

  :global(.feedback-filter:hover) {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark'] .feedback-filter) {
    color: var(--color-gray-200);
  }

  :global(.feedback-export) {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 4px;
    block-size: 32px;
    padding: 6px 8px;
    border-radius: 12px;
    font-size: var(--text-caption);
    transition: background-color 150ms;
  }

  :global(.feedback-export:hover) {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark'] .feedback-export) {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark'] .feedback-export:hover) {
    background-color: var(--color-gray-850);
  }

  :global(.feedback-menu) {
    z-index: 9999;
    min-inline-size: 170px;
  }

  :global(.feedback-menu.narrow) {
    min-inline-size: 150px;
  }

  .grow {
    flex: 1;
  }

  .hidden {
    visibility: hidden;
  }

  .clamp {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  table {
    padding-inline: 8px;
  }

  td {
    padding: 4px 12px;
  }

  .user {
    padding-block: 2px;
  }

  .avatar {
    display: grid;
    place-items: center;
    inline-size: 20px;
    block-size: 20px;
    margin-inline: auto;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-200);
    color: var(--color-white);
  }

  .model {
    padding-block: 6px;
    color: var(--color-gray-600);
    font-size: var(--text-ui);
  }

  .siblings {
    margin-block-start: 2px;
    color: var(--color-gray-600);
    font-size: 0.65rem;
  }

  :global([data-theme='dark']) :is(.model, .siblings) {
    color: var(--color-gray-400);
  }

  .result,
  .updated,
  .menu-cell {
    text-align: end;
  }

  .chip {
    margin-inline-end: 2px;
    padding-inline: 5px;
    border-radius: 8px;
    font-size: var(--text-caption);
    text-transform: uppercase;
  }

  .chip[data-tone='info'] {
    background-color: color-mix(in srgb, var(--color-blue-500) 20%, transparent);
    color: var(--color-blue-700);
  }

  .chip[data-tone='muted'] {
    background-color: color-mix(in srgb, var(--color-gray-500) 20%, transparent);
    color: var(--color-gray-700);
  }

  .chip[data-tone='error'] {
    background-color: color-mix(in srgb, var(--color-red-500) 20%, transparent);
    color: var(--color-red-700);
  }

  :global([data-theme='dark']) .chip[data-tone='info'] {
    color: var(--color-blue-200);
  }

  :global([data-theme='dark']) .chip[data-tone='muted'] {
    color: var(--color-gray-200);
  }

  :global([data-theme='dark']) .chip[data-tone='error'] {
    color: var(--color-red-200);
  }

  :global(.feedback-more) {
    display: inline-grid;
    padding: 6px;
    border-radius: 12px;
  }

  :global(.feedback-more:hover) {
    background-color: rgb(0 0 0 / 0.05);
  }

  :global([data-theme='dark'] .feedback-more) {
    color: var(--color-gray-300);
  }

  :global([data-theme='dark'] .feedback-more:hover) {
    background-color: rgb(255 255 255 / 0.05);
    color: var(--color-white);
  }

  .empty {
    max-inline-size: 384px;
    margin-inline: auto;
    padding: 64px 0 96px;
    text-align: center;
  }

  .empty-title {
    color: var(--color-gray-900);
    font-size: var(--text-ui);
  }

  :global([data-theme='dark']) .empty-title {
    color: var(--color-gray-100);
  }

  .empty-hint {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 20px;
  }
</style>
