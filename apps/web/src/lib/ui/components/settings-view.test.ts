import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import SettingsDialog from './SettingsDialog.svelte';

const setup = () => {
  const source = createFakeSource({ pace: 0 });
  const onclose = vi.fn();
  return {
    source,
    onclose,
    ...render(SettingsDialog, { props: { open: true, source, admin: false, onclose } }),
  };
};

describe('settings dialog (chat-composer F91)', () => {
  it("opens on General and lists the person's tabs under their captions", async () => {
    const { findByRole, getByRole } = setup();
    expect(await findByRole('heading', { name: 'General', level: 2 })).toBeTruthy();
    const nav = getByRole('navigation', { name: 'Settings' });
    for (const name of [
      'General',
      'Interface',
      'Notifications',
      'Keyboard',
      'Personalization',
      'Audio',
      'Data Controls',
      'Usage',
      'Archived Chats',
      'Account',
    ]) {
      expect(within(nav).getByRole('button', { name })).toBeTruthy();
    }
    expect(within(nav).queryByRole('button', { name: 'Connections' })).toBeNull();
    expect(within(nav).getByText('Basics')).toBeTruthy();
  });

  it('filters the tabs by search and says when none match', async () => {
    const { findByPlaceholderText, getByRole, findByText } = setup();
    await fireEvent.input(await findByPlaceholderText('Search'), { target: { value: 'aud' } });
    const nav = getByRole('navigation', { name: 'Settings' });
    expect(
      within(nav)
        .getAllByRole('button')
        .map((b) => b.textContent?.trim()),
    ).toEqual(['Back', 'Audio']);
    await fireEvent.input(await findByPlaceholderText('Search'), { target: { value: 'zzz' } });
    expect(await findByText('No matches')).toBeTruthy();
  });

  it('closes from Back', async () => {
    const { findByRole, onclose } = setup();
    await fireEvent.click(await findByRole('button', { name: 'Back' }));
    expect(onclose).toHaveBeenCalled();
  });
});

describe('general settings (F92)', () => {
  it('saves the system prompt and custom parameters', async () => {
    const { findByPlaceholderText, getByRole, getByText, source } = setup();
    await fireEvent.input(await findByPlaceholderText('Enter system prompt here'), {
      target: { value: 'Be brief.' },
    });
    await fireEvent.click(getByRole('button', { name: 'Show' }));
    const temperature = getByText('Temperature').closest('[data-param]') as HTMLElement;
    await fireEvent.click(within(temperature).getByRole('button', { name: 'Default' }));
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect(await source.getUserSettings()).toEqual({
        system: 'Be brief.',
        params: { temperature: 0.8 },
      }),
    );
  });

  it('offers the themes, OLED Dark included', async () => {
    const { findByRole } = setup();
    const theme = await findByRole('combobox', { name: 'Theme' });
    expect([...(theme as HTMLSelectElement).options].map((o) => o.value)).toEqual([
      'system',
      'dark',
      'oled-dark',
      'light',
    ]);
  });
});
