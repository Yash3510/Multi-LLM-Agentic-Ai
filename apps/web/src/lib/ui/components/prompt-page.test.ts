import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import PromptPage from './PromptPage.svelte';

const setup = async () => {
  const source = createFakeSource({ pace: 0 });
  const made = await source.createPrompt({
    name: 'Summarise',
    command: 'summarise',
    content: 'Summarise {{topic}} in 50 words.',
    tags: [],
  });
  await source.addVersion(made.id, {
    content: 'Summarise {{topic}} in 30 words.',
    message: 'Shorter',
    live: true,
  });
  const prompt = (await source.getPrompt(made.id))!;
  const view = render(PromptPage, { props: { prompt, source } });
  await view.findByText('Shorter');
  return { source, prompt, ...view };
};

afterEach(() => vi.useRealTimers());

describe('prompt page (workspace F95 to F97)', () => {
  it('shows the prompt, its history and the live text', async () => {
    const { getByDisplayValue, getByText, prompt } = await setup();
    expect(getByDisplayValue('Summarise')).toBeTruthy();
    expect(getByDisplayValue('summarise')).toBeTruthy();
    expect(getByText(prompt.id)).toBeTruthy();
    expect(getByText('Initial version')).toBeTruthy();
    expect(getByText('Summarise {{topic}} in 30 words.')).toBeTruthy();
  });

  it('shows an older version and makes it live', async () => {
    const { getByText, findByText, getByRole, source, prompt } = await setup();
    await fireEvent.click(getByText('Initial version'));
    expect(await findByText('Summarise {{topic}} in 50 words.')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Set as Production' }));
    await waitFor(async () =>
      expect((await source.getPrompt(prompt.id))?.content).toBe('Summarise {{topic}} in 50 words.'),
    );
  });

  it('saves an edit as a new live version', async () => {
    const { getByRole, findByText } = await setup();
    await fireEvent.click(getByRole('button', { name: 'Edit' }));
    const dialog = getByRole('dialog');
    await fireEvent.input(within(dialog).getByRole('textbox', { name: 'Prompt Content' }), {
      target: { value: 'Summarise {{topic}} briefly.' },
    });
    await fireEvent.input(within(dialog).getByPlaceholderText('Describe what changed...'), {
      target: { value: 'Brief' },
    });
    await fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }));
    expect(await findByText('Brief')).toBeTruthy();
    expect(await findByText('Summarise {{topic}} briefly.')).toBeTruthy();
  });

  it('puts back a command that breaks the rule', async () => {
    const { getByDisplayValue, findByRole } = await setup();
    vi.useFakeTimers();
    const command = getByDisplayValue('summarise') as HTMLInputElement;
    await fireEvent.input(command, { target: { value: 'bad command' } });
    await vi.advanceTimersByTimeAsync(500);
    vi.useRealTimers();
    expect((await findByRole('alert')).textContent).toContain('Only alphanumeric characters');
    expect(command.value).toBe('summarise');
  });
});
