import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import type { Feedback } from '$lib/data';
import { createFakeSource } from '$lib/data/fake';
import Leaderboard from './Leaderboard.svelte';
import FeedbackList from './FeedbackList.svelte';

const record = (id: string, result: 1 | 0 | -1): Feedback => ({
  id,
  userId: 'u-asha',
  userName: 'Asha Rao',
  modelId: '4ce-tony',
  siblings: ['qwen/qwen3-1.7b'],
  result,
  reason: 'Clear answer',
  tags: ['clear'],
  prompt: 'What changed?',
  response: 'The torque spec.',
  created: new Date(),
  updated: new Date(),
});

describe('leaderboard (admin F95 to F113)', () => {
  it('lists every model with dashes until rated, and searches', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByText, getAllByRole, getByRole, queryByText } = render(Leaderboard, {
      props: { source },
    });
    expect(await findByText('4CE / TONY (Orchestrator)')).toBeTruthy();
    expect(getAllByRole('row')).toHaveLength(4);
    expect(getByRole('columnheader', { name: /RK/ }).getAttribute('aria-sort')).toBe('descending');
    await fireEvent.input(getByRole('textbox', { name: 'Search' }), {
      target: { value: 'qwen3-vl' },
    });
    await waitFor(() => expect(queryByText('4CE / TONY (Orchestrator)')).toBeNull());
  });

  it('opens a model with its activity and tags', async () => {
    const source = createFakeSource({ pace: 0, feedback: [record('f1', 1)] });
    const { findByText, findByRole } = render(Leaderboard, { props: { source } });
    await fireEvent.click(await findByText('4CE / TONY (Orchestrator)'));
    const dialog = await findByRole('dialog', { name: '4CE / TONY (Orchestrator)' });
    expect(within(dialog).getByText('Activity')).toBeTruthy();
    expect(await within(dialog).findByText('clear')).toBeTruthy();
    expect(await within(dialog).findByRole('img', { name: /Won/ })).toBeTruthy();
  });
});

describe('feedback (admin F114 to F132)', () => {
  it('shows the empty state', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByText } = render(FeedbackList, { props: { source } });
    expect(await findByText('No feedback found')).toBeTruthy();
  });

  it('lists feedback with its result, opens details, and deletes with Undo', async () => {
    const source = createFakeSource({ pace: 0, feedback: [record('f1', 1), record('f2', -1)] });
    const { findAllByText, findByRole, getAllByRole, findByText, getByRole } = render(
      FeedbackList,
      {
        props: { source },
      },
    );
    expect(await findAllByText('Won')).toHaveLength(1);
    await fireEvent.click(getAllByRole('row')[1]);
    const details = await findByRole('dialog', { name: 'Feedback Details' });
    expect(within(details).getByText('Clear answer')).toBeTruthy();
    await fireEvent.click(
      within(details).getAllByRole('button', { name: 'Close' }).at(-1) as HTMLElement,
    );

    await fireEvent.click(getAllByRole('button', { name: 'More' })[0]);
    await fireEvent.click(await findByRole('menuitem', { name: 'Delete' }));
    await fireEvent.click(
      within(await findByRole('alertdialog')).getByRole('button', { name: 'Delete' }),
    );
    await waitFor(async () => expect(await source.listFeedback()).toHaveLength(1));
    await fireEvent.click(await findByText('Undo'));
    await waitFor(async () => expect(await source.listFeedback()).toHaveLength(2));
    expect(getByRole('button', { name: /Export/ })).toBeTruthy();
  });
});
