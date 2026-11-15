<script lang="ts">
  // Analytics (admin look §17, F257 to F267): totals for the chosen period, daily assistant
  // messages as a line (plain SVG, no chart library), and messages by model and by person.
  import type { Analytics, DataSource } from '$lib/data';
  import { compact } from '$lib/ui/usage';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Logomark from './Logomark.svelte';
  import SettingsSelect from './SettingsSelect.svelte';
  import './admin-table.css';
  import './settings-page.css';

  type Props = { source: DataSource };

  let { source }: Props = $props();

  const PERIODS = [
    { value: '7', label: 'Last 7 days' },
    { value: '30', label: 'Last 30 days' },
    { value: '90', label: 'Last 90 days' },
    { value: '0', label: 'All time' },
  ];
  let period = $state('7');
  let data = $state<Analytics>();

  $effect(() => {
    const days = Number(period);
    void source.getAnalytics(days).then((loaded) => (data = loaded));
  });

  const peak = $derived(Math.max(1, ...(data?.daily ?? []).map((day) => day.messages)));
  const points = $derived(
    (data?.daily ?? [])
      .map((day, index, all) => {
        const x = all.length > 1 ? (index / (all.length - 1)) * 1000 : 0;
        const y = 180 - (day.messages / peak) * 170;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' '),
  );
  const short = (date: string) => {
    const [, month, day] = date.split('-').map(Number);
    return `${month}/${day}`;
  };
</script>

<div class="settings-page analytics admin-table">
  <div class="head">
    <h2>Analytics</h2>
    <SettingsSelect
      label="Period"
      value={period}
      options={PERIODS}
      onchange={(value) => (period = value)}
    />
  </div>
  {#if data}
    <div class="body">
      <p class="totals">
        <span><strong>{data.totals.messages}</strong> messages</span>
        <span><strong>{compact(data.totals.tokens)}</strong> tokens</span>
        <span><strong>{data.totals.chats}</strong> chats</span>
        <span><strong>{data.totals.users}</strong> users</span>
      </p>
      <h3 class="caption">Daily Messages</h3>
      <svg
        class="chart"
        viewBox="0 0 1000 180"
        preserveAspectRatio="none"
        role="img"
        aria-label="Daily messages"
      >
        <polyline {points} fill="none" vector-effect="non-scaling-stroke" />
      </svg>
      <div class="dates">
        {#each data.daily as day, index (day.date)}
          {#if index % Math.max(1, Math.round(data.daily.length / 7)) === 0 || index === data.daily.length - 1}
            <span style:left="{(index / Math.max(1, data.daily.length - 1)) * 100}%"
              >{short(day.date)}</span
            >
          {/if}
        {/each}
      </div>
      <div class="tables">
        <section>
          <h3 class="caption">Model Usage</h3>
          <div class="scroller">
            <table>
              <thead>
                <tr
                  ><th>#</th><th>Model</th><th class="end">Messages</th><th class="end">Users</th
                  ><th class="end">Chats</th></tr
                >
              </thead>
              <tbody>
                {#each data.models as model, index (model.id)}
                  <tr>
                    <td class="rank">{index + 1}</td>
                    <td
                      ><span class="who"
                        ><Logomark size={20} /><span class="clamp">{model.name}</span></span
                      ></td
                    >
                    <td class="end">{model.messages}</td>
                    <td class="end">{model.users}</td>
                    <td class="end">{model.chats}</td>
                  </tr>
                {:else}
                  <tr><td colspan="5" class="none">No data</td></tr>
                {/each}
              </tbody>
            </table>
          </div>
        </section>
        <section>
          <h3 class="caption">User Activity</h3>
          <div class="scroller">
            <table>
              <thead>
                <tr
                  ><th>#</th><th>User</th><th class="end">Messages</th><th class="end">Tokens</th
                  ></tr
                >
              </thead>
              <tbody>
                {#each data.users as person, index (person.id)}
                  <tr>
                    <td class="rank">{index + 1}</td>
                    <td
                      ><span class="who"
                        ><span class="avatar"><Icon name="user" size={12} /></span
                        >{person.name}</span
                      ></td
                    >
                    <td class="end">{person.messages}</td>
                    <td class="end">{compact(person.tokens)}</td>
                  </tr>
                {:else}
                  <tr><td colspan="4" class="none">No data</td></tr>
                {/each}
              </tbody>
            </table>
          </div>
          <p class="hint">
            <Icon name="info" size={12} /> Message counts are based on assistant responses.
          </p>
        </section>
      </div>
    </div>
  {/if}
</div>

<style>
  .analytics {
    justify-content: flex-start;
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block-end: 4px;
    /* Clear of the panel's close button. */
    padding-inline-end: 28px;
  }

  .head h2 {
    margin: 0;
  }

  .totals {
    display: flex;
    gap: 12px;
    padding-inline: 2px;
    color: var(--color-gray-500);
    font-size: 13px;
  }

  .totals strong {
    color: var(--color-gray-900);
    font-weight: 400;
  }

  :global([data-theme='dark']) .totals strong {
    color: var(--color-white);
  }

  .caption {
    margin: 12px 2px 8px;
    color: var(--color-gray-700);
    font-size: 13px;
    font-weight: 400;
  }

  :global([data-theme='dark']) .caption {
    color: var(--color-gray-300);
  }

  /* The chart and each table are outlined groups, like the settings groups. The line is ink:
     colour is kept for live work. */
  .chart {
    display: block;
    inline-size: 100%;
    block-size: 180px;
    padding: 10px 6px 4px;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-inset);
    background-color: var(--glass-soft);
  }

  .chart polyline {
    stroke: var(--color-ink-1);
    stroke-width: 1.5;
  }

  .dates {
    position: relative;
    block-size: 16px;
    margin-block-start: 6px;
    color: var(--color-gray-400);
    font-size: 10px;
  }

  .dates span {
    position: absolute;
    white-space: nowrap;
    transform: translateX(-50%);
  }

  .dates span:first-child {
    transform: none;
  }

  .dates span:last-child {
    transform: translateX(-100%);
  }

  .tables {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
    margin-block-start: 8px;
  }

  .tables section + section {
    margin-block-start: 0;
  }

  .scroller {
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-inset);
    background-color: var(--glass-soft);
  }

  .analytics thead {
    border-block-end: 0;
    color: var(--color-ink-3);
    text-transform: none;
  }

  th {
    font-weight: var(--font-weight-medium);
  }

  td {
    border-block-start: 1px solid var(--color-line-1);
  }

  td {
    padding: 6px 12px;
  }

  .rank {
    color: var(--color-gray-400);
  }

  .who {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .who {
    color: var(--color-white);
  }

  .clamp {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .avatar {
    display: grid;
    place-items: center;
    inline-size: 20px;
    block-size: 20px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-200);
    color: var(--color-white);
  }

  td.end {
    text-align: end;
  }

  .none {
    color: var(--color-gray-500);
    text-align: center;
  }
</style>
