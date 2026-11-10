<script lang="ts">
  // Create or edit a calendar event (calendar look §1): title, all day, start and end, repeat,
  // reminder, location, description and calendar. Delete when editing.
  import { Dialog } from 'bits-ui';
  import type { Calendar, CalendarEvent } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import Switch from './Switch.svelte';
  import './admin-dialog.css';
  import './modal.css';

  type Draft = Omit<CalendarEvent, 'id'> & { id?: string };
  type Props = {
    open: boolean;
    event?: Draft;
    calendars: Calendar[];
    onsave: (event: Draft) => void;
    ondelete: () => void;
    onclose: () => void;
  };

  let { open, event, calendars, onsave, ondelete, onclose }: Props = $props();

  let draft = $state<Draft>();
  let problem = $state('');

  $effect(() => {
    if (open && event) {
      draft = structuredClone($state.snapshot(event) as Draft);
      problem = '';
    }
  });

  const pad = (value: number) => String(value).padStart(2, '0');
  const local = (date: Date) =>
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;

  function submit(submitEvent: SubmitEvent) {
    submitEvent.preventDefault();
    if (!draft) return;
    if (!draft.title.trim()) {
      problem = 'Title is required';
      return;
    }
    onsave($state.snapshot(draft) as Draft);
  }
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog small">
        <div class="head">
          <Dialog.Title>
            {#snippet child({ props })}<h3 {...props} class="title">
                {event?.id ? 'Edit Event' : 'Create Event'}
              </h3>{/snippet}
          </Dialog.Title>
          <Dialog.Close class="close" aria-label="Close"><Icon name="x" size={16} /></Dialog.Close>
        </div>
        {#if draft}
          <form class="body" onsubmit={submit}>
            <input
              class="event-title"
              bind:value={draft.title}
              placeholder="Event title"
              aria-label="Event title"
            />
            <div class="line">
              <span class="label">All day</span><Switch
                on={draft.allDay}
                label="All day"
                onchange={(next) => draft && (draft.allDay = next)}
              />
            </div>
            <label class="line"
              ><span class="label">Start</span>
              <input
                class="plain small"
                type="datetime-local"
                value={local(draft.start)}
                oninput={(e) => draft && (draft.start = new Date(e.currentTarget.value))}
              /></label
            >
            <label class="line"
              ><span class="label">End</span>
              <input
                class="plain small"
                type="datetime-local"
                value={local(draft.end)}
                oninput={(e) => draft && (draft.end = new Date(e.currentTarget.value))}
              /></label
            >
            <label class="line"
              ><span class="label">Repeat</span>
              <select class="plain small" bind:value={draft.repeat}>
                <option value="none">No Repeat</option><option value="daily">Daily</option><option
                  value="weekly">Weekly</option
                ><option value="monthly">Monthly</option><option value="yearly">Yearly</option>
              </select></label
            >
            <label class="line"
              ><span class="label">Reminder</span>
              <select class="plain small" bind:value={draft.reminder}>
                <option value="none">None</option><option value="0">At time of event</option><option
                  value="5">5 minutes before</option
                ><option value="10">10 minutes before</option><option value="15"
                  >15 minutes before</option
                ><option value="30">30 minutes before</option><option value="60"
                  >1 hour before</option
                >
              </select></label
            >
            <label class="line"
              ><span class="label">Calendar</span>
              <select class="plain small" bind:value={draft.calendarId}>
                {#each calendars as calendar (calendar.id)}<option value={calendar.id}
                    >{calendar.name}</option
                  >{/each}
              </select></label
            >
            <input
              class="plain field"
              bind:value={draft.location}
              placeholder="Add location"
              aria-label="Location"
            />
            <textarea
              class="plain field"
              bind:value={draft.description}
              placeholder="Add description"
              aria-label="Description"
              rows="2"></textarea>
            {#if problem}<p class="problem" role="alert">{problem}</p>{/if}
            <div class="actions">
              {#if event?.id}<button type="button" class="delete" onclick={ondelete}>Delete</button
                >{:else}<span></span>{/if}
              <button type="submit" class="pill">{event?.id ? 'Save' : 'Create'}</button>
            </div>
          </form>
        {/if}
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  .body {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 4px 16px 16px;
  }
  .event-title {
    background: transparent;
    color: inherit;
    font-size: var(--text-base);
  }
  .event-title:focus {
    outline: none;
  }
  .line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .line .label {
    margin: 0;
  }
  .small {
    inline-size: auto;
    font-size: var(--text-caption);
    text-align: end;
  }
  .field {
    font-size: var(--text-ui);
    resize: none;
  }
  .actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-block-start: 8px;
  }
  .delete {
    color: var(--color-gray-500);
    font-size: var(--text-ui);
  }
  .delete:hover {
    color: var(--color-gray-700);
    text-decoration: underline;
  }
</style>
