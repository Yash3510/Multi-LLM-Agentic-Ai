import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import AutomationList from './AutomationList.svelte';
import AutomationEditor from './AutomationEditor.svelte';

const draft = {
  name: 'Morning summary',
  prompt: 'Summarise yesterday',
  model: '4ce-tony',
  schedule: { kind: 'daily' as const, time: '09:00' },
  destination: 'chat' as const,
  active: true,
};

describe('automations (automations look §2)', () => {
  it('shows the empty state, then lists, pauses, runs and deletes with Undo', async () => {
    const empty = render(AutomationList, { props: { source: createFakeSource({ pace: 0 }) } });
    expect(await empty.findByText('No automations')).toBeTruthy();
    empty.unmount();
    const source = createFakeSource({ pace: 0 });
    await source.saveAutomation(draft);
    const { findByText, getByRole, findByRole, queryByText } = render(AutomationList, {
      props: { source },
    });
    expect(await findByText('Daily at 9:00 AM')).toBeTruthy();
    await fireEvent.click(getByRole('switch', { name: 'Morning summary' }));
    await waitFor(async () => expect((await source.listAutomations())[0].active).toBe(false));
    await fireEvent.click(getByRole('button', { name: 'More' }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Run now' }));
    await waitFor(async () => expect((await source.listAutomations())[0].runs).toHaveLength(1));
    await fireEvent.click(getByRole('button', { name: 'More' }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Delete' }));
    await fireEvent.click(await findByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(queryByText('Morning summary')).toBeNull());
    await fireEvent.click(await findByRole('button', { name: 'Undo' }));
    expect(await findByText('Morning summary')).toBeTruthy();
  });

  it('creates an automation from the editor', async () => {
    const source = createFakeSource({ pace: 0 });
    const onsaved = vi.fn();
    const { getByPlaceholderText, getByRole } = render(AutomationEditor, {
      props: { source, onsaved },
    });
    await fireEvent.input(getByPlaceholderText('Automation name'), {
      target: { value: 'Morning summary' },
    });
    await fireEvent.input(getByPlaceholderText('What should the model do each time?'), {
      target: { value: 'Summarise' },
    });
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(onsaved).toHaveBeenCalled());
    expect((await source.listAutomations())[0].name).toBe('Morning summary');
  });
});
