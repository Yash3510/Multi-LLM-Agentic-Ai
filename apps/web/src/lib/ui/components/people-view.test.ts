import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import PeopleList from './PeopleList.svelte';

const setup = async () => {
  const source = createFakeSource({ pace: 0 });
  await source.addUser({
    name: 'Ravi Kumar',
    email: 'ravi@plant.test',
    password: 'demo-only-3',
    role: 'user',
  });
  await source.addUser({
    name: 'Meera Iyer',
    email: 'meera@plant.test',
    password: 'demo-only-4',
    role: 'pending',
  });
  return { source, ...render(PeopleList, { props: { source } }) };
};

describe('people list (admin F9 to F27)', () => {
  it('lists people with their roles, searches and sorts', async () => {
    const { findByText, getByRole, queryByText, getAllByRole } = await setup();
    expect(await findByText('Ravi Kumar')).toBeTruthy();
    expect(getByRole('button', { name: 'Change User Role: Pending' })).toBeTruthy();
    await fireEvent.input(getByRole('textbox', { name: 'Search' }), { target: { value: 'meera' } });
    await waitFor(() => expect(queryByText('Ravi Kumar')).toBeNull());
    await fireEvent.click(getByRole('button', { name: 'Clear search' }));
    await fireEvent.click(getByRole('button', { name: 'Name' }));
    const names = getAllByRole('row')
      .slice(1)
      .map((row) => within(row).getAllByRole('cell')[0].textContent?.trim());
    expect(names).toEqual([...names].sort((a, b) => (a ?? '').localeCompare(b ?? '')));
  });

  it('deletes a person only after typing their email, and can undo', async () => {
    const { findByText, findByRole, queryByText, source } = await setup();
    const row = (await findByText('Ravi Kumar')).closest('tr') as HTMLElement;
    await fireEvent.click(within(row).getByRole('button', { name: 'Delete User' }));
    const dialog = await findByRole('alertdialog');
    const confirm = within(dialog).getByRole('button', { name: 'Delete' });
    expect((confirm as HTMLButtonElement).disabled).toBe(true);
    await fireEvent.input(within(dialog).getByRole('textbox'), {
      target: { value: 'ravi@plant.test' },
    });
    expect((confirm as HTMLButtonElement).disabled).toBe(false);
    await fireEvent.click(confirm);
    await waitFor(() => expect(queryByText('Ravi Kumar')).toBeNull());
    await fireEvent.click(await findByRole('button', { name: 'Undo' }));
    expect(await findByText('Ravi Kumar')).toBeTruthy();
    expect((await source.adminLedger())[0].action).toBe('user.restore');
  });

  it('offers no delete for admins', async () => {
    const { findAllByRole } = await setup();
    const rows = await findAllByRole('row');
    const admin = rows.find((row) => row.textContent?.includes('Admin')) as HTMLElement;
    expect(within(admin).queryByRole('button', { name: 'Delete User' })).toBeNull();
  });
});
