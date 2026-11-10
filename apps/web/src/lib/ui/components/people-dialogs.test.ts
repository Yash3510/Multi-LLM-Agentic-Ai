import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import AddUserDialog from './AddUserDialog.svelte';
import EditUserDialog from './EditUserDialog.svelte';
import AccessPreviewDialog from './AccessPreviewDialog.svelte';

describe('add user dialog (admin F28 to F36)', () => {
  it('adds a person from the form, password hidden until shown', async () => {
    const source = createFakeSource({ pace: 0 });
    const onsaved = vi.fn();
    const { findByRole, getByLabelText, getByRole } = render(AddUserDialog, {
      props: { open: true, source, onsaved, onclose: vi.fn() },
    });
    const dialog = await findByRole('dialog', { name: 'Add User' });
    expect(
      (within(dialog).getByRole('combobox', { name: 'Role' }) as HTMLSelectElement).value,
    ).toBe('user');
    await fireEvent.input(getByLabelText('Name'), { target: { value: 'Ravi Kumar' } });
    await fireEvent.input(getByLabelText('Email'), { target: { value: 'ravi@plant.test' } });
    const password = getByLabelText('Password') as HTMLInputElement;
    expect(password.type).toBe('password');
    await fireEvent.click(getByRole('button', { name: 'Show password' }));
    expect(password.type).toBe('text');
    await fireEvent.input(password, { target: { value: 'demo-only-8' } });
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(onsaved).toHaveBeenCalled());
    expect((await source.listUsers()).some((one) => one.email === 'ravi@plant.test')).toBe(true);
  });

  it('shows the server message and stays open for a taken email', async () => {
    const source = createFakeSource({ pace: 0 });
    const onsaved = vi.fn();
    const { getByLabelText, getByRole, findByText } = render(AddUserDialog, {
      props: { open: true, source, onsaved, onclose: vi.fn() },
    });
    await fireEvent.input(getByLabelText('Name'), { target: { value: 'Dup' } });
    await fireEvent.input(getByLabelText('Email'), { target: { value: 'admin@4ce.local' } });
    await fireEvent.input(getByLabelText('Password'), { target: { value: 'demo-only-9' } });
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    expect(await findByText(/already exists/)).toBeTruthy();
    expect(onsaved).not.toHaveBeenCalled();
  });

  it('imports people from a CSV file and reports bad rows', async () => {
    const source = createFakeSource({ pace: 0 });
    const { getByRole, findByText, container } = render(AddUserDialog, {
      props: { open: true, source, onsaved: vi.fn(), onclose: vi.fn() },
    });
    await fireEvent.click(getByRole('button', { name: 'CSV Import' }));
    const input = container.ownerDocument.querySelector('input[accept=".csv"]') as HTMLInputElement;
    const file = new File(
      ['Name,Email,Password,Role\nA One,a@plant.test,demo-only-10,user\nbroken'],
      'people.csv',
      { type: 'text/csv' },
    );
    await fireEvent.change(input, { target: { files: [file] } });
    expect(await findByText('1 document(s) selected.')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    expect(await findByText('Successfully imported 1 users.')).toBeTruthy();
    expect(await findByText('Row 3: expected Name, Email, Password, Role.')).toBeTruthy();
  });
});

describe('edit user dialog (admin F37 to F44)', () => {
  it('saves a role change and keeps your own role locked', async () => {
    const source = createFakeSource({ pace: 0 });
    const added = await source.addUser({
      name: 'Ravi Kumar',
      email: 'ravi@plant.test',
      password: 'demo-only-11',
      role: 'user',
    });
    const onsaved = vi.fn();
    const view = render(EditUserDialog, {
      props: { open: true, source, person: added, selfId: 'u-asha', onsaved, onclose: vi.fn() },
    });
    expect(await view.findByText('Created at', { exact: false })).toBeTruthy();
    await fireEvent.change(view.getByRole('combobox', { name: 'Role' }), {
      target: { value: 'admin' },
    });
    await fireEvent.click(view.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(onsaved).toHaveBeenCalled());
    expect((await source.listUsers()).find((one) => one.id === added.id)?.role).toBe('admin');
    view.unmount();

    const [self] = await source.listUsers();
    const mine = render(EditUserDialog, {
      props: { open: true, source, person: self, selfId: self.id, onsaved, onclose: vi.fn() },
    });
    expect(
      ((await mine.findByRole('combobox', { name: 'Role' })) as HTMLSelectElement).disabled,
    ).toBe(true);
  });
});

describe('access preview dialog (admin F50 to F53)', () => {
  it('lists what a person can reach', async () => {
    const source = createFakeSource({ pace: 0 });
    const [, other] = await source.listUsers();
    const { findByRole, findByText, getByText } = render(AccessPreviewDialog, {
      props: { open: true, source, person: other, onclose: vi.fn() },
    });
    const dialog = await findByRole('dialog', { name: /User Preview/ });
    expect(within(dialog).getByText(other.name)).toBeTruthy();
    expect(await findByText('Models')).toBeTruthy();
    expect(getByText('Knowledge')).toBeTruthy();
    expect(getByText('Tools')).toBeTruthy();
  });
});
