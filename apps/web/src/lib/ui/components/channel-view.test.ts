import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import ChannelView from './ChannelView.svelte';

const setup = async () => {
  const source = createFakeSource({ pace: 0 });
  const [channel] = await source.listChannels();
  return {
    source,
    channel,
    ...render(ChannelView, { props: { source, channel, selfId: 'u-asha' } }),
  };
};

describe('channel view (channels look §3)', () => {
  it('shows the channel, its pinned message and members', async () => {
    const { findByText, getByRole, getAllByText } = await setup();
    expect(await findByText('Welcome to the general channel.')).toBeTruthy();
    expect(getAllByText('Pinned').length).toBeGreaterThan(0);
    expect(getByRole('button', { name: 'Users' }).textContent).toContain('2');
  });

  it('sends with Enter, replies, reacts, and deletes after confirming', async () => {
    const {
      findByText,
      getByPlaceholderText,
      getAllByRole,
      findByRole,
      queryByText,
      source,
      channel,
    } = await setup();
    const box = getByPlaceholderText('Message #general');
    await fireEvent.input(box, { target: { value: 'Hello team' } });
    await fireEvent.keyDown(box, { key: 'Enter' });
    const mine = (await findByText('Hello team')).closest('[data-message]') as HTMLElement;
    await fireEvent.click(within(mine).getByRole('button', { name: 'Add Reaction' }));
    await waitFor(async () =>
      expect((await source.listChannelMessages(channel.id)).at(-1)?.reactions['👍']).toEqual([
        'u-asha',
      ]),
    );
    await fireEvent.click(within(mine).getByRole('button', { name: 'Reply' }));
    expect(await findByText(/Replying to/)).toBeTruthy();
    await fireEvent.click(within(mine).getByRole('button', { name: 'Delete' }));
    await fireEvent.click(
      within(await findByRole('alertdialog')).getByRole('button', { name: 'Confirm' }),
    );
    await waitFor(() => expect(queryByText('Hello team')).toBeNull());
    expect(getAllByRole('button', { name: 'Pin' }).length).toBeGreaterThan(0);
  });
});
