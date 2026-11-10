<script lang="ts">
  // The calendar (calendar look §1): the month with its events, a mini month and the calendars
  // beside it, Today and Create. Events open in a dialog; deleting offers Undo. Outside calendar
  // sync is left out, as the owner chose.
  import { untrack } from 'svelte';
  import type { Calendar, CalendarEvent, DataSource } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import EventDialog from './EventDialog.svelte';

  type Props = { source: DataSource; today?: Date };

  let { source, today = new Date() }: Props = $props();

  type Draft = Omit<CalendarEvent, 'id'> & { id?: string };
  // The month on show starts at today's; the page re-creates the view to change "today".
  const firstOfToday = untrack(() => new Date(today.getFullYear(), today.getMonth(), 1));
  let shown = $state(firstOfToday);
  let mini = $state(firstOfToday);
  let calendars = $state<Calendar[]>([]);
  let hiddenCalendars = $state<string[]>([]);
  let events = $state<CalendarEvent[]>([]);
  let editing = $state<Draft>();
  let undo = $state<CalendarEvent>();

  async function load() {
    [calendars, events] = await Promise.all([source.listCalendars(), source.listEvents()]);
  }
  void load();

  const title = (month: Date) =>
    month.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const sameDay = (a: Date, b: Date) => a.toDateString() === b.toDateString();
  /** The 42 days of a month's six-week grid, starting on Sunday. */
  const cells = (month: Date) => {
    const first = new Date(month.getFullYear(), month.getMonth(), 1);
    return Array.from(
      { length: 42 },
      (_, index) => new Date(first.getFullYear(), first.getMonth(), index - first.getDay() + 1),
    );
  };
  const step = (month: Date, by: number) => new Date(month.getFullYear(), month.getMonth() + by, 1);
  const colour = (id: string) => calendars.find((one) => one.id === id)?.color ?? 'blue';
  const dayEvents = (day: Date) =>
    events
      .filter((one) => sameDay(one.start, day) && !hiddenCalendars.includes(one.calendarId))
      .sort((a, b) => a.start.getTime() - b.start.getTime());

  function create(day = today) {
    const start = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 9);
    editing = {
      calendarId: calendars[0]?.id ?? 'personal',
      title: '',
      start,
      end: new Date(start.getTime() + 3_600_000),
      allDay: false,
      repeat: 'none',
      reminder: 'none',
      location: '',
      description: '',
    };
  }

  async function save(draft: Draft) {
    editing = undefined;
    await source.saveEvent(draft);
    await load();
  }

  async function remove() {
    const id = editing?.id;
    if (!id) return;
    undo = events.find((one) => one.id === id);
    editing = undefined;
    await source.deleteEvent(id);
    await load();
  }

  async function restore() {
    if (!undo) return;
    await source.restoreEvent(undo.id);
    undo = undefined;
    await load();
  }

  async function addCalendar() {
    await source.createCalendar({
      name: `Calendar ${calendars.length + 1}`,
      color: ['green', 'purple', 'orange', 'rose'][calendars.length % 4],
    });
    await load();
  }
</script>

<div class="calendar">
  <header class="top">
    <h1>{title(shown)}</h1>
    <button
      type="button"
      class="caret"
      aria-label="Previous month"
      onclick={() => (shown = step(shown, -1))}><Icon name="caret-left" size={14} /></button
    >
    <button
      type="button"
      class="caret"
      aria-label="Next month"
      onclick={() => (shown = step(shown, 1))}><Icon name="caret-right" size={14} /></button
    >
    <span class="grow"></span>
    {#if undo}<span class="undo" role="status"
        >Deleted {undo.title}. <button type="button" onclick={restore}>Undo</button></span
      >{/if}
    <button
      type="button"
      class="text"
      onclick={() => (shown = new Date(today.getFullYear(), today.getMonth(), 1))}>Today</button
    >
    <span class="text">Month</span>
    <button type="button" class="create" onclick={() => create()}>Create</button>
  </header>
  <div class="layout">
    <aside class="side">
      <div class="mini-head">
        <span>{title(mini)}</span>
        <button
          type="button"
          class="caret"
          aria-label="Previous mini month"
          onclick={() => (mini = step(mini, -1))}><Icon name="caret-left" size={12} /></button
        >
        <button
          type="button"
          class="caret"
          aria-label="Next mini month"
          onclick={() => (mini = step(mini, 1))}><Icon name="caret-right" size={12} /></button
        >
      </div>
      <div class="mini">
        {#each ['S', 'M', 'T', 'W', 'T', 'F', 'S'] as letter, index (index)}<span class="letter"
            >{letter}</span
          >{/each}
        {#each cells(mini) as day (day.toISOString())}
          <button
            type="button"
            class="mini-day"
            class:other={day.getMonth() !== mini.getMonth()}
            class:today={sameDay(day, today)}
            onclick={() => (shown = new Date(day.getFullYear(), day.getMonth(), 1))}
            >{day.getDate()}</button
          >
        {/each}
      </div>
      <div class="calendars-head">
        <span>Calendars</span>
        <button type="button" class="caret" aria-label="Add calendar" onclick={addCalendar}
          ><Icon name="plus" size={16} /></button
        >
      </div>
      {#each calendars as calendar (calendar.id)}
        <label class="calendar-row">
          <input
            type="checkbox"
            checked={!hiddenCalendars.includes(calendar.id)}
            onchange={(e) =>
              (hiddenCalendars = e.currentTarget.checked
                ? hiddenCalendars.filter((one) => one !== calendar.id)
                : [...hiddenCalendars, calendar.id])}
          />
          <span class="dot" style:background-color="var(--color-{calendar.color}-500)"
          ></span>{calendar.name}
        </label>
      {/each}
    </aside>
    <div class="month">
      <div class="weekdays">
        {#each ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as name (name)}<span>{name}</span
          >{/each}
      </div>
      <div class="grid">
        {#each cells(shown) as day (day.toISOString())}
          <div
            class="cell"
            role="button"
            tabindex="0"
            aria-label={day.toDateString()}
            ondblclick={() => create(day)}
            onkeydown={(e) => e.key === 'Enter' && create(day)}
          >
            <span
              class="number"
              class:other={day.getMonth() !== shown.getMonth()}
              class:today={sameDay(day, today)}>{day.getDate()}</span
            >
            {#each dayEvents(day).slice(0, 3) as event (event.id)}
              <button
                type="button"
                class="chip"
                style:--hue="var(--color-{colour(event.calendarId)}-500)"
                onclick={(e) => {
                  e.stopPropagation();
                  editing = event;
                }}>{event.title}</button
              >
            {/each}
            {#if dayEvents(day).length > 3}<span class="more"
                >+{dayEvents(day).length - 3} more</span
              >{/if}
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

<EventDialog
  open={editing !== undefined}
  event={editing}
  {calendars}
  onsave={save}
  ondelete={remove}
  onclose={() => (editing = undefined)}
/>

<style>
  .calendar {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    padding: 0 12px 12px;
    font-size: var(--text-ui);
  }
  .top {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 4px;
  }
  h1 {
    font-size: var(--text-ui);
    font-weight: 400;
  }
  .caret {
    display: grid;
    place-items: center;
    color: var(--color-gray-400);
  }
  .grow {
    flex: 1;
  }
  .text {
    color: var(--color-gray-500);
    font-size: 13px;
  }
  .create {
    padding: 4px 10px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    box-shadow: 0 0 0 1px var(--color-gray-200);
    font-size: var(--text-caption);
  }
  :global([data-theme='dark']) .create {
    background-color: var(--color-gray-850);
    box-shadow: 0 0 0 1px var(--color-gray-800);
  }
  .undo {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .undo button {
    color: inherit;
    text-decoration: underline;
  }
  .layout {
    display: flex;
    flex: 1;
    gap: 20px;
    min-block-size: 0;
  }
  .side {
    display: none;
    flex: none;
    inline-size: 220px;
    padding-block-start: 8px;
  }
  @media (min-width: 64rem) {
    .side {
      display: block;
    }
  }
  .mini-head {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: var(--text-caption);
  }
  .mini-head span {
    flex: 1;
  }
  .mini {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0;
    margin-block: 8px 24px;
    text-align: center;
  }
  .letter {
    color: var(--color-gray-500);
    font-size: 10px;
    line-height: 24px;
  }
  .mini-day {
    block-size: 24px;
    border-radius: var(--radius-pill);
    font-size: 11px;
  }
  .mini-day.other {
    color: var(--color-gray-300);
  }
  .mini-day.today,
  .number.today {
    background-color: var(--color-blue-500);
    color: var(--color-white);
  }
  .calendars-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--color-gray-500);
    font-size: 11px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .calendar-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-block: 4px;
    font-size: var(--text-caption);
  }
  .dot {
    inline-size: 8px;
    block-size: 8px;
    border-radius: var(--radius-pill);
  }
  .month {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
  }
  .weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    padding: 0 0 6px 18px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .grid {
    display: grid;
    flex: 1;
    grid-template-columns: repeat(7, 1fr);
    grid-template-rows: repeat(6, 1fr);
    overflow: hidden;
    border: 1px solid var(--color-gray-50);
    border-radius: 12px;
  }
  :global([data-theme='dark']) .grid,
  :global([data-theme='dark']) .cell {
    border-color: var(--color-gray-850);
  }
  .cell {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-inline-size: 0;
    padding: 8px 10px;
    border-block-start: 1px solid var(--color-gray-50);
    border-inline-start: 1px solid var(--color-gray-50);
  }
  .number {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    border-radius: var(--radius-pill);
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .number.other {
    color: var(--color-gray-300);
  }
  .chip {
    overflow: hidden;
    padding: 1px 4px;
    border-radius: 4px;
    background-color: color-mix(in srgb, var(--hue) 15%, transparent);
    color: var(--hue);
    font-size: 11px;
    text-align: start;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .more {
    color: var(--color-gray-500);
    font-size: 11px;
  }
  :is(.caret, .text, .create, .mini-day, .chip, .cell, .undo button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
