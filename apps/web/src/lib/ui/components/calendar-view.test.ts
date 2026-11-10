import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import CalendarView from './CalendarView.svelte';

describe('calendar (calendar look §1)', () => {
  it('shows the month, creates an event on a day, and deletes it with Undo', async () => {
    const source = createFakeSource({ pace: 0 });
    const today = new Date(2026, 10, 10);
    const { getByText, getByRole, findByRole, findByText, queryByText } = render(CalendarView, {
      props: { source, today },
    });
    expect(getByText('November 2026', { selector: 'h1' })).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Create' }));
    const dialog = await findByRole('dialog', { name: 'Create Event' });
    await fireEvent.input(within(dialog).getByPlaceholderText('Event title'), {
      target: { value: 'Review' },
    });
    await fireEvent.click(within(dialog).getByRole('button', { name: 'Create' }));
    expect(await findByText('Review')).toBeTruthy();
    await fireEvent.click(getByText('Review'));
    const edit = await findByRole('dialog', { name: 'Edit Event' });
    await fireEvent.click(within(edit).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(queryByText('Review')).toBeNull());
    await fireEvent.click(await findByRole('button', { name: 'Undo' }));
    expect(await findByText('Review')).toBeTruthy();
  });

  it('moves between months', async () => {
    const source = createFakeSource({ pace: 0 });
    const { getByRole, getByText } = render(CalendarView, {
      props: { source, today: new Date(2026, 10, 10) },
    });
    await fireEvent.click(getByRole('button', { name: 'Next month' }));
    expect(getByText('December 2026', { selector: 'h1' })).toBeTruthy();
  });
});
