import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import PlaygroundChat from './PlaygroundChat.svelte';
import PlaygroundCompletions from './PlaygroundCompletions.svelte';

describe('playground (playground look §3)', () => {
  it('adds a user message and runs for an assistant reply', async () => {
    const source = createFakeSource({ pace: 0 });
    const { getByPlaceholderText, getByRole, findByText, findAllByLabelText } = render(
      PlaygroundChat,
      { props: { source } },
    );
    await fireEvent.input(getByPlaceholderText('Enter a user message here'), {
      target: { value: 'Hi there' },
    });
    await fireEvent.click(getByRole('button', { name: 'Run' }));
    expect(await findByText('Hi there')).toBeTruthy();
    await waitFor(async () => expect((await findAllByLabelText('Message')).length).toBe(2));
    expect(await findByText(/sample reply/)).toBeTruthy();
  });

  it('continues text in completions', async () => {
    const source = createFakeSource({ pace: 0 });
    const { getByRole } = render(PlaygroundCompletions, { props: { source } });
    const box = getByRole('textbox') as HTMLTextAreaElement;
    await fireEvent.input(box, { target: { value: 'Once upon' } });
    await fireEvent.click(getByRole('button', { name: 'Run' }));
    await waitFor(() => expect(box.value.length).toBeGreaterThan('Once upon'.length));
  });
});
