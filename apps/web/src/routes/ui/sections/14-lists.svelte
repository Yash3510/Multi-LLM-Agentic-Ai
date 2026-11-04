<script module lang="ts">
  import type { SectionMeta } from '../section';

  // English until the ui_section_lists and ui_lists_* messages exist; the captions below are the
  // same. Demo data is sector-neutral: rules R2 to R6, ids like CASE-0142.
  export const section: SectionMeta = {
    id: 'lists',
    title: () => 'Lists',
    description: () =>
      'List rows, recency headings, sortable column headers and the short time-ago, in every state.',
  };
</script>

<script lang="ts">
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import GroupHeading from '$lib/ui/components/GroupHeading.svelte';
  import ListRow from '$lib/ui/components/ListRow.svelte';
  import SortHeader from '$lib/ui/components/SortHeader.svelte';
  import { nextSort, type Sort } from '$lib/ui/components/sort';
  import { formatAgo, timeGroup, toIntlLocale, type TimeGroup } from '$lib/ui/format';

  const locale = toIntlLocale(getLocale());

  // A fixed "now", so the stills read the same on every visit.
  const NOW = new Date(2026, 10, 4, 10, 30);
  const at = (days: number, hours = 0) => new Date(NOW.getTime() - (days * 24 + hours) * 3_600_000);

  const ITEMS = [
    { id: 'CASE-0142', title: 'R2 · Ratio check', updated: at(0, 1) },
    { id: 'CASE-0143', title: 'R3 · Duration review', updated: at(0, 5) },
    { id: 'CASE-0139', title: 'R4 · Cost of the second batch', updated: at(1, 2) },
    { id: 'CASE-0131', title: 'R5 · Tolerance', updated: at(4) },
    { id: 'CASE-0120', title: 'R6 · Limits', updated: at(19) },
    { id: 'CASE-0101', title: 'R2 · Ratio, first revision', updated: at(52) },
    { id: 'CASE-0077', title: 'R3 · Duration, archived', updated: at(400) },
  ];

  let sort = $state<Sort>({ column: 'updated', direction: 'descending' });

  const sorted = $derived(
    [...ITEMS].sort((a, b) => {
      const order =
        sort.column === 'title'
          ? a.title.localeCompare(b.title, locale)
          : a.updated.getTime() - b.updated.getTime();
      return sort.direction === 'ascending' ? order : -order;
    }),
  );

  const sameGroup = (a?: TimeGroup, b?: TimeGroup) => JSON.stringify(a) === JSON.stringify(b);

  // Headings only while sorted by time: under a title sort the bands would repeat out of order.
  const rows = $derived(
    sorted.map((item, index) => {
      const group = timeGroup(item.updated, NOW);
      const before = index > 0 ? timeGroup(sorted[index - 1].updated, NOW) : undefined;
      const heading = sort.column === 'updated' && !sameGroup(group, before) ? group : undefined;
      return { ...item, heading, first: index === 0 };
    }),
  );

  // The side list: the last 30 days, newest first.
  const recent = ITEMS.filter((item) => item.updated > at(30));

  const date = new Intl.DateTimeFormat(locale, { day: 'numeric', month: 'short', year: 'numeric' });

  const onsort = (column: string) => {
    sort = nextSort(sort, column, column === 'updated' ? 'descending' : 'ascending');
  };
</script>

<div class="flex flex-col gap-10">
  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">List dialog</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          Press a header to sort; press it again to flip. Recency headings show only while sorted by
          time. Rows take the faint tint on hover
        </dt>
        <dd>
          <div class="frame" role="table" aria-label="Cases">
            <div class="headers" role="row">
              <div class="title-cell">
                <SortHeader column="title" label="Title" {sort} {onsort} />
              </div>
              <div class="date-cell">
                <SortHeader column="updated" label="Updated" {sort} {onsort} align="end" />
              </div>
            </div>
            <div role="rowgroup">
              {#each rows as row (row.id)}
                {#if row.heading}
                  <!-- Inside a table a heading needs a row and cell of its own. -->
                  <div role="row">
                    <div role="cell">
                      <GroupHeading group={row.heading} first={row.first} level={4} />
                    </div>
                  </div>
                {/if}
                <ListRow role="row">
                  <span class="title-cell truncate" role="cell">
                    <a class="stretch" href="#lists">{row.title}</a>
                  </span>
                  <span class="date-cell date" role="cell">{date.format(row.updated)}</span>
                </ListRow>
              {/each}
            </div>
          </div>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Side list</h3>
    <dl class="rows">
      <div class="row">
        <dt>32 px rows, 13 px titles, the short time-ago at the end; the open case is current</dt>
        <dd>
          <div class="side">
            {#each recent as row, index (row.id)}
              {@const group = timeGroup(row.updated, NOW)}
              {#if group && (index === 0 || !sameGroup(group, timeGroup(recent[index - 1].updated, NOW)))}
                <GroupHeading {group} first={index === 0} variant="sidebar" level={4} />
              {/if}
              <ListRow href="/ui#lists" variant="sidebar" current={row.id === 'CASE-0143'}>
                <span class="truncate">{row.title}</span>
                <time class="ago" datetime={row.updated.toISOString()}>
                  {formatAgo(row.updated, { now: NOW, locale })}
                </time>
              </ListRow>
            {/each}
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>Time-ago: the largest whole unit, never under a minute</dt>
        <dd class="ago-samples">
          {#each [0, 0.75, 5, 30, 200, 900, 9000] as hours (hours)}
            <code>{formatAgo(at(0, hours), { now: NOW, locale })}</code>
          {/each}
        </dd>
      </div>
    </dl>
  </div>
</div>

<style>
  /* Caption on the left, examples on the right; stacked when narrow. */
  .rows {
    display: flex;
    flex-direction: column;
  }

  .row {
    display: grid;
    gap: var(--spacing-2) var(--spacing-6);
    padding-block: var(--spacing-3);
    border-top: 1px solid var(--color-line-1);
  }

  @media (min-width: 48rem) {
    .row {
      grid-template-columns: 14rem minmax(0, 1fr);
      align-items: start;
    }
  }

  dt {
    font-size: var(--text-caption);
    line-height: var(--text-caption--line-height);
    color: var(--color-ink-3);
  }

  dd {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--spacing-3);
    min-width: 0;
  }

  .frame {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    max-inline-size: 36rem;
    padding: var(--spacing-3) var(--spacing-5) var(--spacing-4);
    border-radius: var(--radius-card);
    background-color: var(--color-surface-raised);
    box-shadow: var(--shadow-e1);
  }

  .headers {
    display: flex;
    margin-block-end: 6px;
  }

  .title-cell {
    flex: 0 0 60%;
    min-inline-size: 0;
  }

  .date-cell {
    flex: 0 0 40%;
    text-align: end;
  }

  /* The title is the row's one link; its hit area stretches over the whole row. */
  .stretch {
    color: inherit;
    text-decoration: none;
  }

  .stretch::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
  }

  .stretch:focus-visible {
    outline: none;
  }

  :global([data-list-row]:has(.stretch:focus-visible)) {
    box-shadow: var(--shadow-focus);
  }

  .date {
    color: var(--color-ink-3);
    font-size: var(--text-caption);
  }

  .side {
    display: flex;
    flex-direction: column;
    inline-size: 16rem;
    padding: 6px var(--spacing-1_5);
    border-radius: var(--radius-card);
    background-color: var(--color-surface-sunken);
    color: var(--color-ink-2);
  }

  .ago {
    flex-shrink: 0;
    padding-inline-start: var(--spacing-2);
    color: var(--color-ink-3);
    font-size: var(--text-nano);
  }

  .ago-samples code {
    color: var(--color-ink-2);
    font-size: var(--text-caption);
  }

  @media (max-width: 40rem) {
    .date-cell {
      display: none;
    }

    .title-cell {
      flex-basis: 100%;
    }
  }
</style>
