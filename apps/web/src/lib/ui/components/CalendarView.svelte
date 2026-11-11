<script lang="ts">
  // The calendar (calendar look §1): the month with its events, a mini month and the calendars
  // beside it, Today and Create. Events open in a dialog; deleting offers Undo. Outside calendar
  // sync is left out, as the owner chose.
  import { untrack } from 'svelte';
  import type { Calendar, CalendarEvent, DataSource } from '$lib/data';
  import { occurrences } from '$lib/ui/calendar';
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
  let view = $state<'month' | 'week' | 'day'>('month');
  // The day the week and day views centre on.
  let focus = $state(
    untrack(() => new Date(today.getFullYear(), today.getMonth(), today.getDate())),
  );
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
  const range = $derived.by(() => {
    if (view === 'month') {
      const all = cells(shown);
      return [all[0], new Date(all[41].getFullYear(), all[41].getMonth(), all[41].getDate() + 1)];
    }
    const start =
      view === 'week'
        ? new Date(focus.getFullYear(), focus.getMonth(), focus.getDate() - focus.getDay())
        : focus;
    return [
      start,
      new Date(start.getFullYear(), start.getMonth(), start.getDate() + (view === 'week' ? 7 : 1)),
    ];
  });
  const visible = $derived(
    occurrences(events, range[0], range[1]).filter(
      (one) => !hiddenCalendars.includes(one.calendarId),
    ),
  );
  const dayEvents = (day: Date) => visible.filter((one) => sameDay(one.start, day));
  const days = $derived(
    Array.from(
      { length: view === 'week' ? 7 : 1 },
      (_, index) =>
        new Date(range[0].getFullYear(), range[0].getMonth(), range[0].getDate() + index),
    ),
  );
  const heading = $derived.by(() => {
    if (view === 'month') return title(shown);
    if (view === 'day')
      return focus.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      });
    const [start] = days;
    const end = days[6];
    const month = (date: Date) => date.toLocaleDateString('en-US', { month: 'short' });
    return start.getMonth() === end.getMonth()
      ? `${month(start)} ${start.getDate()} – ${end.getDate()}, ${end.getFullYear()}`
      : `${month(start)} ${start.getDate()} – ${month(end)} ${end.getDate()}, ${end.getFullYear()}`;
  });
  const HOURS = Array.from({ length: 24 }, (_, hour) => hour);
  const hourLabel = (hour: number) =>
    new Date(2000, 0, 1, hour).toLocaleTimeString('en-US', { hour: 'numeric' });

  function move(by: number) {
    if (view === 'month') shown = step(shown, by);
    else
      focus = new Date(
        focus.getFullYear(),
        focus.getMonth(),
        focus.getDate() + by * (view === 'week' ? 7 : 1),
      );
  }

  function goToday() {
    shown = new Date(today.getFullYear(), today.getMonth(), 1);
    focus = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  }

  /** Opens the stored event behind an occurrence. */
  const open = (occurrence: CalendarEvent) =>
    (editing = events.find((one) => one.id === occurrence.id) ?? occurrence);

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
  <header class="top" data-page-bar>
    <h1>{heading}</h1>
    <button type="button" class="caret" aria-label="Previous month" onclick={() => move(-1)}
      ><Icon name="caret-left" size={14} /></button
    >
    <button type="button" class="caret" aria-label="Next month" onclick={() => move(1)}
      ><Icon name="caret-right" size={14} /></button
    >
    <span class="grow"></span>
    {#if undo}<span class="undo" role="status"
        >Deleted {undo.title}. <button type="button" onclick={restore}>Undo</button></span
      >{/if}
    <button type="button" class="text" onclick={goToday}>Today</button>
    <select class="text view" bind:value={view} aria-label="View">
      <option value="month">Month</option><option value="week">Week</option><option value="day"
        >Day</option
      >
    </select>
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
    {#if view !== 'month'}
      <div class="hours">
        <div class="hours-head">
          <span class="gutter-head"></span>
          {#each days as day (day.toISOString())}
            <span class="hours-day" class:today={sameDay(day, today)}>
              {day.toLocaleDateString('en-US', { weekday: 'short' })}
              {day.getDate()}
            </span>
          {/each}
        </div>
        <div class="hours-body">
          <div class="hour-labels">
            {#each HOURS as hour (hour)}<span>{hourLabel(hour)}</span>{/each}
          </div>
          {#each days as day (day.toISOString())}
            <div
              class="hour-column"
              role="button"
              tabindex="0"
              aria-label={day.toDateString()}
              ondblclick={() => create(day)}
              onkeydown={(e) => e.key === 'Enter' && create(day)}
            >
              {#each HOURS as hour (hour)}<span class="hour-line"></span>{/each}
              {#each dayEvents(day) as event (event.id + event.start.toISOString())}
                <button
                  type="button"
                  class="block"
                  style:--hue="var(--color-{colour(event.calendarId)}-500)"
                  style:top="{(event.start.getHours() + event.start.getMinutes() / 60) * 48}px"
                  style:height="{Math.max(
                    20,
                    ((event.end.getTime() - event.start.getTime()) / 3_600_000) * 48,
                  )}px"
                  onclick={(e) => {
                    e.stopPropagation();
                    open(event);
                  }}>{event.title}</button
                >
              {/each}
            </div>
          {/each}
        </div>
      </div>
    {:else}
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
              {#each dayEvents(day).slice(0, 3) as event (event.id + event.start.toISOString())}
                <button
                  type="button"
                  class="chip"
                  style:--hue="var(--color-{colour(event.calendarId)}-500)"
                  onclick={(e) => {
                    e.stopPropagation();
                    open(event);
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
    {/if}
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
    border-radius: var(--radius-pill);
    box-shadow:
      var(--gloss-edge),
      0 0 0 1px var(--color-gray-200);
    background-image: var(--gloss-fill);
  }
  .create {
    padding: 4px 10px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-50);
    box-shadow:
      var(--gloss-edge),
      0 0 0 1px var(--color-gray-200);
    font-size: var(--text-caption);
    background-image: var(--gloss-fill);
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
  .view {
    appearance: none;
    background: transparent;
  }
  .hours {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
    overflow: hidden;
    border: 1px solid var(--color-gray-50);
    border-radius: 12px;
  }
  :global([data-theme='dark']) .hours,
  :global([data-theme='dark']) .hour-line,
  :global([data-theme='dark']) .hour-column {
    border-color: var(--color-gray-850);
  }
  .hours-head {
    display: flex;
    padding-block: 8px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .gutter-head,
  .hour-labels {
    flex: none;
    inline-size: 56px;
  }
  .hours-day {
    flex: 1;
    text-align: center;
  }
  .hours-day.today {
    color: var(--color-blue-500);
  }
  .hours-body {
    display: flex;
    flex: 1;
    overflow-y: auto;
  }
  .hour-labels span {
    display: block;
    block-size: 48px;
    padding-inline-end: 8px;
    color: var(--color-gray-400);
    font-size: 10px;
    text-align: end;
    transform: translateY(-6px);
  }
  .hour-column {
    position: relative;
    flex: 1;
    border-inline-start: 1px solid var(--color-gray-50);
  }
  .hour-line {
    display: block;
    block-size: 48px;
    border-block-start: 1px solid var(--color-gray-50);
  }
  .block {
    position: absolute;
    inset-inline: 2px;
    overflow: hidden;
    padding: 2px 4px;
    border-radius: 4px;
    background-color: color-mix(in srgb, var(--hue) 15%, transparent);
    color: var(--hue);
    font-size: 11px;
    text-align: start;
  }
  .more {
    color: var(--color-gray-500);
    font-size: 11px;
  }
  /* Hover states (common look, Motion: calendar): 150 ms on the standard curve. */
  :is(.caret, .text, .create, .mini-day, .chip, .cell, .block, .calendar-row) {
    transition-property: background-color, color;
    transition-duration: 150ms;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }

  .caret {
    padding: 2px;
    border-radius: var(--radius-pill);
  }

  .text {
    padding: 4px 10px;
    border-radius: var(--radius-pill);
  }

  :is(.caret, .mini-day:not(.today)):hover {
    background-color: var(--color-gray-100);
  }

  .text:hover {
    background-color: var(--color-gray-50);
    color: var(--color-gray-700);
  }

  .create:hover {
    background-color: var(--color-gray-100);
  }

  .cell:hover {
    background-color: color-mix(in srgb, var(--color-gray-50) 50%, transparent);
  }

  :is(.chip, .block):hover {
    background-color: color-mix(in srgb, var(--hue) 25%, transparent);
  }

  .calendar-row:hover {
    background-color: var(--color-gray-50);
  }

  :global([data-theme='dark']) :is(.caret, .mini-day:not(.today)):hover {
    background-color: var(--color-gray-800);
  }

  :global([data-theme='dark']) .text:hover {
    background-color: var(--color-gray-850);
    color: var(--color-white);
  }

  :global([data-theme='dark']) .create:hover {
    background-color: var(--color-gray-800);
  }

  :global([data-theme='dark']) .cell:hover {
    background-color: color-mix(in srgb, var(--color-gray-850) 20%, transparent);
  }

  :global([data-theme='dark']) .calendar-row:hover {
    background-color: color-mix(in srgb, var(--color-gray-800) 50%, transparent);
  }

  :is(.caret, .text, .create, .mini-day, .chip, .cell, .undo button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
