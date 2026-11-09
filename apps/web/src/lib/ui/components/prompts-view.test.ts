import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import CreatePromptDialog from './CreatePromptDialog.svelte';
import PromptList from './PromptList.svelte';

const prompts = [
  {
    id: 'p1',
    name: 'Summarise',
    command: 'summarise',
    content: 'Summarise {{topic}} in 50 words.',
    tags: [],
    active: true,
    updated: new Date(Date.now() - 3 * 86_400_000),
    owner: { name: 'asha rao' },
    writable: true,
    liveVersion: 'v1',
  },
];

describe('prompt list (workspace F89 to F92)', () => {
  it('shows each prompt with its command, age, text and owner', () => {
    const { getByText } = render(PromptList, { props: { prompts } });
    expect(getByText('/summarise')).toBeTruthy();
    expect(getByText('3 days ago')).toBeTruthy();
    expect(getByText('Summarise {{topic}} in 50 words.')).toBeTruthy();
    expect(getByText('Asha rao')).toBeTruthy();
  });

  it('says when nothing matches', async () => {
    const { getByPlaceholderText, findByText } = render(PromptList, { props: { prompts } });
    await fireEvent.input(getByPlaceholderText('Search Prompts'), { target: { value: 'zzz' } });
    expect(await findByText('No prompts found')).toBeTruthy();
  });

  it('switches a prompt on and off', async () => {
    const ontoggle = vi.fn();
    const { getByRole } = render(PromptList, { props: { prompts, ontoggle } });
    await fireEvent.click(getByRole('switch', { name: 'Enabled' }));
    expect(ontoggle).toHaveBeenCalledWith('p1', false);
  });

  it('deletes at once while Shift is held', async () => {
    const ondelete = vi.fn();
    const { getByRole } = render(PromptList, { props: { prompts, ondelete } });
    await fireEvent.keyDown(window, { key: 'Shift' });
    await fireEvent.click(getByRole('button', { name: 'Delete' }));
    expect(ondelete).toHaveBeenCalledWith('p1');
  });
});

describe('create prompt dialog (F93)', () => {
  it('follows the name with the command until the command is typed', async () => {
    const { getByPlaceholderText } = render(CreatePromptDialog, {
      props: { open: true, oncreate: vi.fn(), onclose: () => {} },
    });
    await fireEvent.input(getByPlaceholderText('Name'), { target: { value: 'Unit Check' } });
    const command = getByPlaceholderText('Command') as HTMLInputElement;
    expect(command.value).toBe('unit-check');
    await fireEvent.input(command, { target: { value: 'mine' } });
    await fireEvent.input(getByPlaceholderText('Name'), { target: { value: 'Unit Check 2' } });
    expect(command.value).toBe('mine');
  });

  it('refuses a command with spaces, then saves', async () => {
    const oncreate = vi.fn(async () => {});
    const { getByPlaceholderText, getByRole, findByRole } = render(CreatePromptDialog, {
      props: { open: true, oncreate, onclose: () => {} },
    });
    await fireEvent.input(getByPlaceholderText('Name'), { target: { value: 'Brief' } });
    await fireEvent.input(getByPlaceholderText('Command'), { target: { value: 'bad command' } });
    await fireEvent.input(getByRole('textbox', { name: 'Prompt Content' }), {
      target: { value: 'Be brief.' },
    });
    await fireEvent.click(getByRole('button', { name: 'Save & Create' }));
    expect((await findByRole('alert')).textContent).toContain('Only alphanumeric characters');
    await fireEvent.input(getByPlaceholderText('Command'), { target: { value: 'brief' } });
    await fireEvent.click(getByRole('button', { name: 'Save & Create' }));
    await waitFor(() =>
      expect(oncreate).toHaveBeenCalledWith({
        name: 'Brief',
        command: 'brief',
        content: 'Be brief.',
        tags: [],
      }),
    );
  });
});
