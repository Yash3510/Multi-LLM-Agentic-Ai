import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import SettingsDialog from './SettingsDialog.svelte';

const open = async (tab: string, nth = 0) => {
  const source = createFakeSource({ pace: 0 });
  const view = render(SettingsDialog, {
    props: { open: true, source, admin: true, onclose: vi.fn() },
  });
  const nav = await view.findByRole('navigation', { name: 'Settings' });
  await fireEvent.click(within(nav).getAllByRole('button', { name: tab })[nth]);
  return { source, ...view };
};

describe('admin settings tabs (admin look §18)', () => {
  it('lists the admin tabs for admins only', async () => {
    const { getByRole, unmount } = await open('General');
    const nav = getByRole('navigation', { name: 'Settings' });
    expect(within(nav).getByText('Admin')).toBeTruthy();
    expect(within(nav).getByRole('button', { name: 'Authentication' })).toBeTruthy();
    expect(within(nav).queryByRole('button', { name: 'Web Search' })).toBeNull();
    unmount();
    const source = createFakeSource({ pace: 0 });
    const plain = render(SettingsDialog, {
      props: { open: true, source, admin: false, onclose: vi.fn() },
    });
    const plainNav = await plain.findByRole('navigation', { name: 'Settings' });
    expect(within(plainNav).queryByRole('button', { name: 'Authentication' })).toBeNull();
  });

  it('saves the general panel, with sub-settings following their switch', async () => {
    const { findByRole, getByRole, queryByText, findByText, source } = await open('General', 1);
    await findByRole('heading', { name: 'General', level: 2 });
    expect(queryByText('Model Response Mode')).toBeNull();
    await fireEvent.click(getByRole('switch', { name: 'Channels' }));
    expect(await findByText('Model Response Mode')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect(await source.getAdminSettings('general')).toMatchObject({ ENABLE_CHANNELS: true }),
    );
  });

  it('shows LDAP as configured by the server', async () => {
    const { findByText, findAllByText } = await open('Authentication');
    expect(await findByText('LDAP', { selector: 'h3' })).toBeTruthy();
    expect((await findAllByText('Configured by the server.')).length).toBe(2);
  });

  it('exports users only after typing EXPORT, and logs it', async () => {
    const { findByRole, findAllByRole, source } = await open('Database');
    await findByRole('heading', { name: 'Database', level: 2 });
    const buttons = await findAllByRole('button', { name: 'Export' });
    await fireEvent.click(buttons.at(-1) as HTMLElement);
    const confirm = await findByRole('alertdialog');
    const ok = within(confirm).getByRole('button', { name: 'Export' }) as HTMLButtonElement;
    expect(ok.disabled).toBe(true);
    await fireEvent.input(within(confirm).getByRole('textbox'), { target: { value: 'EXPORT' } });
    URL.createObjectURL = vi.fn(() => 'blob:x');
    URL.revokeObjectURL = vi.fn();
    await fireEvent.click(ok);
    await waitFor(async () => expect((await source.adminLedger())[0].action).toBe('export.users'));
  });
});

describe('admin models and analytics (admin look §17, §23)', () => {
  it('disables a model, saves, and resets only after typing RESET with Undo', async () => {
    const { findByText, getByRole, findByRole, source } = await open('Models');
    expect(await findByText('4CE / TONY (Orchestrator)')).toBeTruthy();
    await fireEvent.click(getByRole('switch', { name: '4CE / TONY (Orchestrator)' }));
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect(await source.getAdminSettings('models')).toMatchObject({ disabled: ['4ce-tony'] }),
    );
    await fireEvent.click(getByRole('button', { name: 'Actions' }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Reset' }));
    const confirm = await findByRole('alertdialog');
    await fireEvent.input(within(confirm).getByRole('textbox'), { target: { value: 'RESET' } });
    await fireEvent.click(within(confirm).getByRole('button', { name: 'Reset' }));
    await waitFor(async () =>
      expect(await source.getAdminSettings('models')).toMatchObject({ disabled: [] }),
    );
    await fireEvent.click(await findByText('Undo'));
    await waitFor(async () =>
      expect(await source.getAdminSettings('models')).toMatchObject({ disabled: ['4ce-tony'] }),
    );
  });

  it('shows analytics totals and the model usage table', async () => {
    const { findByText, getByText, getAllByText } = await open('Analytics');
    expect(await findByText('Daily Messages')).toBeTruthy();
    expect(getAllByText('4.4k')).toHaveLength(2);
    expect(getByText('Model Usage')).toBeTruthy();
    expect(
      getByText('Message counts are based on assistant responses.', { exact: false }),
    ).toBeTruthy();
  });

  it('says pipelines are not detected', async () => {
    const { findByText } = await open('Pipelines');
    expect(await findByText('Pipelines Not Detected')).toBeTruthy();
  });
});

describe('admin settings leftovers', () => {
  it('adds a banner and a default interface setting in General', async () => {
    const { findByRole, getByRole, source, findByText } = await open('General', 1);
    await findByRole('heading', { name: 'General', level: 2 });
    await fireEvent.click(getByRole('button', { name: 'Add banner' }));
    await fireEvent.input(getByRole('textbox', { name: 'Banner text' }), {
      target: { value: 'Maintenance at 6 PM' },
    });
    await fireEvent.click(getByRole('button', { name: 'Configure' }));
    await fireEvent.click(getByRole('switch', { name: 'Widescreen Mode' }));
    expect(await findByText('1 settings configured')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () => {
      const values = await source.getAdminSettings('general');
      expect(values.BANNERS).toMatchObject([{ content: 'Maintenance at 6 PM', type: 'info' }]);
      expect(values.DEFAULT_INTERFACE).toEqual({ widescreen: true });
    });
  });

  it('adds an arena model in Evaluations', async () => {
    const { findByRole, getByRole, source } = await open('Evaluations');
    await findByRole('heading', { name: 'Evaluations', level: 2 });
    await fireEvent.click(getByRole('switch', { name: 'Arena Models' }));
    await fireEvent.click(getByRole('button', { name: 'Add Arena Model' }));
    await fireEvent.input(getByRole('textbox', { name: 'Arena model name' }), {
      target: { value: 'Blind test' },
    });
    await fireEvent.click(getByRole('button', { name: 'Add' }));
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect((await source.getAdminSettings('evaluations')).ARENA_MODELS).toMatchObject([
        { name: 'Blind test' },
      ]),
    );
  });
});
