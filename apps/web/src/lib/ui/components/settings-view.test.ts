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

describe('interface settings (F93, common F68)', () => {
  it('saves a changed preference and opens Manage for quick actions', async () => {
    const { findByRole, getByRole, getByText, findByText, source } = setup();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Interface' }));
    expect(await findByRole('heading', { name: 'Interface', level: 2 })).toBeTruthy();
    const row = getByText('Accessibility Mode').closest('.block') as HTMLElement;
    await fireEvent.click(within(row).getByRole('switch'));
    await fireEvent.click(getByRole('button', { name: 'Manage' }));
    expect(await findByText('Default action buttons will be used.')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Close modal' }));
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect((await source.getUserSettings()).ui).toMatchObject({ accessibility: true }),
    );
  });
});

describe('notifications settings (F94)', () => {
  it('saves Notification Sound at once', async () => {
    const { getByRole, findByText, source } = setup();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Notifications' }));
    const row = (await findByText('Notification Sound')).closest('.block') as HTMLElement;
    await fireEvent.click(within(row).getByRole('switch'));
    await waitFor(async () =>
      expect((await source.getUserSettings()).ui).toMatchObject({ notificationSound: false }),
    );
  });
});

describe('keyboard settings (F95)', () => {
  it('rebinds a shortcut, refuses a taken chord, and resets', async () => {
    const { getByRole, findByText, source } = setup();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Keyboard' }));
    const row = (await findByText('Navigate to Next Chat')).closest('.shortcut') as HTMLElement;
    await fireEvent.click(within(row).getByRole('button', { name: /Unassigned/ }));
    expect(within(row).getByText('Press keys...')).toBeTruthy();
    await fireEvent.keyDown(window, { key: 'j', ctrlKey: true, metaKey: true });
    await waitFor(async () =>
      expect(
        ((await source.getUserSettings()).ui as Record<string, unknown>)?.shortcuts,
      ).toMatchObject({
        nextChat: { key: 'j' },
      }),
    );
    const search = (await findByText('Previous Chat', { exact: false })).closest(
      '.shortcut',
    ) as HTMLElement;
    await fireEvent.click(within(search).getByRole('button', { name: /Unassigned/ }));
    await fireEvent.keyDown(window, { key: 'j', ctrlKey: true, metaKey: true });
    expect(await findByText('Already bound to Navigate to Next Chat')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Reset Defaults' }));
    await waitFor(async () =>
      expect(((await source.getUserSettings()).ui as Record<string, unknown>)?.shortcuts).toEqual(
        {},
      ),
    );
  });
});

describe('personalization settings (F98)', () => {
  it('adds, searches, edits and removes a memory, and clears them all', async () => {
    const { getByRole, findByRole, findByText, findByPlaceholderText, queryByText, source } =
      setup();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Personalization' }));
    expect(await findByText('Memories accessible by LLMs will be shown here.')).toBeTruthy();

    await fireEvent.click(await findByRole('button', { name: 'Actions' }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Add Memory' }));
    const add = await findByRole('dialog', { name: 'Add Memory' });
    await fireEvent.click(within(add).getByRole('button', { name: 'User' }));
    expect(within(add).getByRole('button', { name: 'Context' })).toBeTruthy();
    await fireEvent.input(
      within(add).getByPlaceholderText('Add durable context for future chats'),
      {
        target: { value: 'Works on line 3' },
      },
    );
    await fireEvent.click(within(add).getByRole('button', { name: 'Add' }));
    expect(await findByText('Works on line 3')).toBeTruthy();
    expect((await source.listMemories())[0]).toMatchObject({ type: 'context' });

    await fireEvent.input(await findByPlaceholderText('Search Memories'), {
      target: { value: 'zzz' },
    });
    expect(await findByText('No results found')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Clear search' }));

    await fireEvent.click(await findByRole('button', { name: 'Edit' }));
    const edit = await findByRole('dialog', { name: 'Edit Memory' });
    await fireEvent.input(within(edit).getByRole('textbox', { name: 'Memory' }), {
      target: { value: 'Works on line 4' },
    });
    await fireEvent.click(within(edit).getByRole('button', { name: 'Update' }));
    expect(await findByText('Works on line 4')).toBeTruthy();

    await fireEvent.click(getByRole('button', { name: 'Remove' }));
    const remove = await findByRole('alertdialog', { name: 'Delete Memory?' });
    expect(within(remove).getByText('Works on line 4')).toBeTruthy();
    await fireEvent.click(within(remove).getByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(queryByText('Works on line 4')).toBeNull());

    await fireEvent.click(await findByRole('button', { name: 'Actions' }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Add Memory' }));
    const again = await findByRole('dialog', { name: 'Add Memory' });
    await fireEvent.input(within(again).getByRole('textbox', { name: 'Memory' }), {
      target: { value: 'One more' },
    });
    await fireEvent.click(within(again).getByRole('button', { name: 'Add' }));
    expect(await findByText('One more')).toBeTruthy();
    await fireEvent.click(await findByRole('button', { name: 'Actions' }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Clear memory' }));
    await fireEvent.click(
      within(await findByRole('alertdialog', { name: 'Clear Memory' })).getByRole('button', {
        name: 'Confirm',
      }),
    );
    await waitFor(async () => expect(await source.listMemories()).toEqual([]));
  });

  it('saves the memory switch at once', async () => {
    const { getByRole, findByText, source } = setup();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Personalization' }));
    const row = (await findByText('Experimental')).closest('.block') as HTMLElement;
    await fireEvent.click(within(row).getByRole('switch'));
    await waitFor(async () =>
      expect((await source.getUserSettings()).ui).toMatchObject({ memory: false }),
    );
    expect(await findByText('Saved Memories').catch(() => null)).toBeNull();
  });
});

describe('audio settings (F99)', () => {
  it('saves the switches at once and the rest with Save, with local engines only', async () => {
    const { getByRole, findByText, findByRole, queryByText, source } = setup();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Audio' }));
    const tts = await findByRole('combobox', { name: 'Text-to-Speech Engine' });
    expect(
      within(tts)
        .getAllByRole('option')
        .map((o) => o.textContent),
    ).toEqual(['Default']);
    expect(queryByText('Allow non-local voices')).toBeNull();

    const send = (await findByText('Instant Auto-Send After Voice Transcription')).closest(
      '.block',
    ) as HTMLElement;
    await fireEvent.click(within(send).getByRole('switch'));
    await waitFor(async () =>
      expect((await source.getUserSettings()).ui).toMatchObject({ speechAutoSend: true }),
    );

    await fireEvent.input(getByRole('textbox', { name: 'Speech-to-Text Language' }), {
      target: { value: 'hi' },
    });
    await fireEvent.input(getByRole('spinbutton', { name: 'Speech Playback Speed' }), {
      target: { value: '1.5' },
    });
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect((await source.getUserSettings()).ui).toMatchObject({
        audio: { sttLanguage: 'hi', playbackRate: 1.5 },
      }),
    );
  });
});

describe('data controls (F100)', () => {
  it('imports a chat file, and archives and deletes all after confirmation', async () => {
    const { getByRole, findByRole, findByText, container, source } = setup();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Data Controls' }));
    expect(await findByRole('heading', { name: 'Data Controls', level: 2 })).toBeTruthy();

    const input = container.ownerDocument.querySelector(
      'input[type="file"][accept=".json"]',
    ) as HTMLInputElement;
    const file = new File([JSON.stringify([{ title: 'From file', messages: [] }])], 'chats.json', {
      type: 'application/json',
    });
    await fireEvent.change(input, { target: { files: [file] } });
    expect(await findByText('Imported 1 chat.')).toBeTruthy();

    const bad = new File(['not json'], 'bad.json', { type: 'application/json' });
    await fireEvent.change(input, { target: { files: [bad] } });
    expect(await findByText('That file is not a chat export.')).toBeTruthy();

    await fireEvent.click(getByRole('button', { name: 'Archive All' }));
    await fireEvent.click(
      within(await findByRole('alertdialog', { name: 'Archive All Chats' })).getByRole('button', {
        name: 'Confirm',
      }),
    );
    await waitFor(async () => expect(await source.listChats()).toEqual([]));

    await fireEvent.click(getByRole('button', { name: 'Delete All' }));
    await fireEvent.click(
      within(await findByRole('alertdialog', { name: 'Delete All Chats' })).getByRole('button', {
        name: 'Confirm',
      }),
    );
    await waitFor(async () => expect(await source.exportChats()).toEqual([]));
  });
});

describe('usage (F101)', () => {
  it('shows the overview, switches the heat map mode and lists top models', async () => {
    const { getByRole, findByText, getByText } = setup();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Usage' }));
    expect((await findByText('Lifetime tokens')).previousElementSibling?.textContent).toBe('50.2k');
    const weekly = getByRole('button', { name: 'Weekly' });
    expect(getByRole('button', { name: 'Daily' }).getAttribute('aria-pressed')).toBe('true');
    await fireEvent.click(weekly);
    expect(weekly.getAttribute('aria-pressed')).toBe('true');
    expect(getByText('6 messages · 50.2k')).toBeTruthy();
    expect(
      getByText('Token counts are estimates and may not reflect actual API usage'),
    ).toBeTruthy();
  });
});

describe('archived chats (F102)', () => {
  it('lists archived chats, searches, unarchives, deletes and unarchives all', async () => {
    const { getByRole, findByRole, findByText, queryByText, source } = setup();
    const chats = await source.listChats();
    await source.archiveAllChats();
    const nav = getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Archived Chats' }));
    const heading = await findByRole('heading', { name: /Archived Chats/, level: 2 });
    expect(heading.textContent).toContain(String(chats.length));
    expect(await findByText(chats[0].title)).toBeTruthy();

    await fireEvent.input(getByRole('textbox', { name: 'Search archived chats' }), {
      target: { value: 'zzz' },
    });
    expect(await findByText('You have no archived conversations.')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Clear search' }));

    const first = (await findByText(chats[0].title)).closest('li') as HTMLElement;
    await fireEvent.click(within(first).getByRole('button', { name: 'Unarchive Chat' }));
    await waitFor(() => expect(queryByText(chats[0].title)).toBeNull());

    const second = (await findByText(chats[1].title)).closest('li') as HTMLElement;
    await fireEvent.click(within(second).getByRole('button', { name: 'Delete Chat' }));
    await fireEvent.click(
      within(await findByRole('alertdialog')).getByRole('button', { name: 'Confirm' }),
    );
    await waitFor(async () => expect(await source.getChat(chats[1].id)).toBeUndefined());

    await fireEvent.click(getByRole('button', { name: 'Actions' }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Unarchive All' }));
    await fireEvent.click(
      within(await findByRole('alertdialog')).getByRole('button', { name: 'Unarchive All' }),
    );
    await waitFor(async () => expect(await source.listArchivedChats()).toEqual([]));
    expect(await findByText('You have no archived conversations.')).toBeTruthy();
  });
});

describe('account (F103)', () => {
  const open = async () => {
    const view = setup();
    const nav = view.getByRole('navigation', { name: 'Settings' });
    await fireEvent.click(within(nav).getByRole('button', { name: 'Account' }));
    await view.findByRole('heading', { name: 'Account', level: 2 });
    return view;
  };

  it('saves the profile and a user variable, refusing a bad key', async () => {
    const { getByRole, findByRole, findByText, source } = await open();
    await fireEvent.input(getByRole('textbox', { name: 'Name' }), {
      target: { value: 'Asha Rao' },
    });
    await fireEvent.change(getByRole('combobox', { name: 'Gender' }), {
      target: { value: 'custom' },
    });
    await fireEvent.input(getByRole('textbox', { name: 'Custom Gender' }), {
      target: { value: 'non-binary' },
    });
    await fireEvent.click(getByRole('button', { name: 'Add' }));
    const dialog = await findByRole('dialog', { name: 'Add User Variable' });
    await fireEvent.input(within(dialog).getByRole('textbox', { name: 'Variable key' }), {
      target: { value: 'Plant Code' },
    });
    await fireEvent.click(within(dialog).getByRole('button', { name: 'Done' }));
    expect(await findByText('Variable keys must use lowercase snake case.')).toBeTruthy();
    await fireEvent.input(within(dialog).getByRole('textbox', { name: 'Variable key' }), {
      target: { value: 'plant_code' },
    });
    await fireEvent.input(within(dialog).getByRole('textbox', { name: 'Variable value' }), {
      target: { value: 'P3' },
    });
    await fireEvent.click(within(dialog).getByRole('button', { name: 'Done' }));
    expect(await findByText('plant_code')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect(await source.getProfile()).toMatchObject({
        name: 'Asha Rao',
        gender: 'non-binary',
        variables: { plant_code: 'P3' },
      }),
    );
  });

  it('switches the avatar to initials and back to the default', async () => {
    const { getByRole, source } = await open();
    await fireEvent.click(getByRole('button', { name: 'Initials' }));
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect((await source.getProfile()).avatar).toEqual({ kind: 'initials' }),
    );
    await fireEvent.click(getByRole('button', { name: 'Remove' }));
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect((await source.getProfile()).avatar).toEqual({ kind: 'default' }),
    );
  });

  it('changes the password when the new one is confirmed', async () => {
    const { getByRole, getByLabelText, findByText, source } = await open();
    const change = vi.spyOn(source, 'changePassword');
    await fireEvent.click(getByRole('button', { name: 'Show' }));
    await fireEvent.input(getByLabelText('Current Password'), { target: { value: 'old-pass' } });
    await fireEvent.input(getByLabelText('New Password'), { target: { value: 'new-pass-1' } });
    await fireEvent.input(getByLabelText('Confirm Password'), { target: { value: 'new-pass-2' } });
    await fireEvent.click(getByRole('button', { name: 'Update password' }));
    expect(
      await findByText(
        "The passwords you entered don't quite match. Please double-check and try again.",
      ),
    ).toBeTruthy();
    expect(change).not.toHaveBeenCalled();
    await fireEvent.input(getByLabelText('Confirm Password'), { target: { value: 'new-pass-1' } });
    await fireEvent.click(getByRole('button', { name: 'Update password' }));
    expect(await findByText('Password updated.')).toBeTruthy();
    expect(change).toHaveBeenCalledWith('old-pass', 'new-pass-1');
    expect((getByLabelText('New Password') as HTMLInputElement).value).toBe('');
  });
});
