import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import GroupList from './GroupList.svelte';
import GroupEditor from './GroupEditor.svelte';

describe('groups list (admin F54 to F63)', () => {
  it('shows the empty state and the default permissions row', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByText, getByRole } = render(GroupList, { props: { source } });
    expect(await findByText('No groups found')).toBeTruthy();
    expect(getByRole('button', { name: /Default permissions/ })).toBeTruthy();
  });

  it('lists groups by members, then by name, and searches', async () => {
    const source = createFakeSource({ pace: 0 });
    const a = await source.createGroup({
      name: 'Alpha',
      description: '',
      share: 'members',
      permissions: {},
    });
    await source.createGroup({
      name: 'Beta',
      description: 'Shift B',
      share: 'members',
      permissions: { chat: { edit: false } },
    });
    await source.setGroupMember(a.id, 'u-admin', true);
    const { findByText, getAllByRole, getByRole, queryByText } = render(GroupList, {
      props: { source },
    });
    expect(await findByText('1 members')).toBeTruthy();
    expect(await findByText('Custom permissions')).toBeTruthy();
    const names = () => getAllByRole('button', { name: /Edit$/ }).map((b) => b.textContent);
    expect(names()[0]).toContain('Alpha');
    await fireEvent.click(getByRole('button', { name: /Members/ }));
    await fireEvent.click(await findByText('Name'));
    await fireEvent.input(getByRole('textbox', { name: 'Search Groups' }), {
      target: { value: 'bet' },
    });
    await waitFor(() => expect(queryByText('Alpha')).toBeNull());
  });
});

describe('group editor (admin F64 to F92)', () => {
  it('creates a group from the General tab', async () => {
    const source = createFakeSource({ pace: 0 });
    const onsaved = vi.fn();
    const { findByRole, getByPlaceholderText, getByRole } = render(GroupEditor, {
      props: { open: true, source, mode: 'create', defaults: {}, onsaved, onclose: vi.fn() },
    });
    expect(await findByRole('dialog', { name: 'Add User Group' })).toBeTruthy();
    expect(getByRole('button', { name: 'Permissions' })).toBeTruthy();
    expect(() => getByRole('button', { name: 'Users' })).toThrow();
    await fireEvent.input(getByPlaceholderText('Group Name'), { target: { value: 'Line 3' } });
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(onsaved).toHaveBeenCalled());
    expect((await source.listGroups())[0].name).toBe('Line 3');
  });

  it('edits permissions, shows the default hint, and toggles members at once', async () => {
    const source = createFakeSource({ pace: 0 });
    const group = await source.createGroup({
      name: 'Line 3',
      description: '',
      share: 'members',
      permissions: {},
    });
    const { findByRole, getByRole, findByText, findAllByRole } = render(GroupEditor, {
      props: {
        open: true,
        source,
        mode: 'edit',
        group,
        defaults: { workspace: { knowledge: true } },
        onsaved: vi.fn(),
        onclose: vi.fn(),
      },
    });
    await findByRole('dialog', { name: 'Edit User Group' });
    await fireEvent.click(getByRole('button', { name: 'Permissions' }));
    expect(
      await findByText('This is a default user permission and will remain enabled.'),
    ).toBeTruthy();
    await fireEvent.click(getByRole('switch', { name: 'Models Access' }));
    expect(getByRole('switch', { name: 'Import Models' })).toBeTruthy();

    await fireEvent.click(getByRole('button', { name: 'Users' }));
    const boxes = await findAllByRole('checkbox');
    await fireEvent.click(boxes[0]);
    await waitFor(async () => expect((await source.listGroups())[0].members).toHaveLength(1));
  });

  it('deletes a group only after typing its name', async () => {
    const source = createFakeSource({ pace: 0 });
    const group = await source.createGroup({
      name: 'Line 3',
      description: '',
      share: 'members',
      permissions: {},
    });
    const ondeleted = vi.fn();
    const { findByRole, getByRole } = render(GroupEditor, {
      props: {
        open: true,
        source,
        mode: 'edit',
        group,
        defaults: {},
        onsaved: vi.fn(),
        ondeleted,
        onclose: vi.fn(),
      },
    });
    await findByRole('dialog', { name: 'Edit User Group' });
    await fireEvent.click(getByRole('button', { name: 'Delete' }));
    const confirm = await findByRole('alertdialog');
    const button = within(confirm).getByRole('button', { name: 'Delete' }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    await fireEvent.input(within(confirm).getByRole('textbox'), { target: { value: 'Line 3' } });
    await fireEvent.click(button);
    await waitFor(() => expect(ondeleted).toHaveBeenCalled());
    expect(await source.listGroups()).toEqual([]);
  });

  it('saves default permissions with only the Permissions tab', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByRole, getByRole, queryByRole } = render(GroupEditor, {
      props: {
        open: true,
        source,
        mode: 'defaults',
        defaults: {},
        onsaved: vi.fn(),
        onclose: vi.fn(),
      },
    });
    await findByRole('dialog', { name: 'Edit Default Permissions' });
    expect(queryByRole('button', { name: 'General' })).toBeNull();
    await fireEvent.click(getByRole('switch', { name: 'API Keys' }));
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect((await source.getDefaultPermissions()).features?.api_keys).toBe(true),
    );
  });
});

describe('group member CSV import (admin F86)', () => {
  it('adds members by email from a CSV file', async () => {
    const source = createFakeSource({ pace: 0 });
    const group = await source.createGroup({
      name: 'Team',
      description: '',
      share: 'members',
      permissions: {},
    });
    const { findByRole, getByRole, container } = render(GroupEditor, {
      props: {
        open: true,
        source,
        mode: 'edit',
        group,
        defaults: {},
        onsaved: vi.fn(),
        onclose: vi.fn(),
      },
    });
    await findByRole('dialog', { name: 'Edit User Group' });
    await fireEvent.click(getByRole('button', { name: 'Users' }));
    const input = container.ownerDocument.querySelector('input[accept=".csv"]') as HTMLInputElement;
    await fireEvent.change(input, {
      target: { files: [new File(['Name,Email\nAdmin,admin@4ce.local\n'], 'm.csv')] },
    });
    await waitFor(async () => expect((await source.listGroups())[0].members).toEqual(['u-admin']));
  });
});
