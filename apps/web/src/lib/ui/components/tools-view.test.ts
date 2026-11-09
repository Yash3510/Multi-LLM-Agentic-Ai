import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import ToolEditor from './ToolEditor.svelte';
import ToolList from './ToolList.svelte';

const tool = {
  id: 'unit_convert',
  name: 'Unit Convert',
  description: 'Converts units.',
  content: 'class Tools: pass',
  version: '0.2.0',
  updated: new Date(Date.now() - 35 * 86_400_000),
  owner: { name: '4CE Administrator' },
  writable: true,
};

describe('tool list (workspace F108 to F111)', () => {
  it('shows the version, age, description and Settings', () => {
    const { getByText, getByRole } = render(ToolList, { props: { tools: [tool] } });
    expect(getByText('v0.2.0')).toBeTruthy();
    expect(getByText('a month ago')).toBeTruthy();
    expect(getByText('Converts units.')).toBeTruthy();
    expect(getByRole('button', { name: 'Settings' })).toBeTruthy();
  });

  it('dims a tool the person cannot change and gives it no controls', () => {
    const { getByText, queryByRole } = render(ToolList, {
      props: { tools: [{ ...tool, writable: false }] },
    });
    expect(getByText('Read Only')).toBeTruthy();
    expect(queryByRole('button', { name: 'Settings' })).toBeNull();
    expect(queryByRole('button', { name: 'Tool Menu' })).toBeNull();
  });
});

describe('tool editor (F114)', () => {
  it('makes the id from the name and asks about the risk before creating', async () => {
    const source = createFakeSource({ pace: 0 });
    const onsaved = vi.fn();
    const { getByPlaceholderText, getByRole, findByText } = render(ToolEditor, {
      props: { source, onsaved },
    });
    await fireEvent.input(getByPlaceholderText('Tool Name'), { target: { value: 'Unit Convert' } });
    expect((getByPlaceholderText('Tool ID') as HTMLInputElement).value).toBe('unit_convert');
    await fireEvent.input(getByPlaceholderText('Tool Description'), {
      target: { value: 'Converts units.' },
    });
    await fireEvent.click(getByRole('button', { name: 'Save & Create' }));
    expect(await findByText('Please carefully review the following warnings:')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Confirm' }));
    await waitFor(async () => expect(await source.getTool('unit_convert')).toBeTruthy());
    expect((await source.getTool('unit_convert'))?.content).toContain('class Tools:');
    expect(onsaved).toHaveBeenCalled();
  });

  it('needs a description, unlike skills', async () => {
    const source = createFakeSource({ pace: 0 });
    const { getByPlaceholderText, getByRole, findByRole } = render(ToolEditor, {
      props: { source },
    });
    await fireEvent.input(getByPlaceholderText('Tool Name'), { target: { value: 'Unit Convert' } });
    await fireEvent.click(getByRole('button', { name: 'Save & Create' }));
    expect((await findByRole('alert')).textContent).toContain('Please fill in all fields.');
  });
});
