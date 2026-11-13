import { fireEvent, render, within } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ModelEditor from './ModelEditor.svelte';

const lists = {
  baseModels: [
    { id: '4ce-tony', name: '4CE / TONY (Orchestrator)' },
    { id: 'qwen/qwen3-1.7b', name: 'qwen/qwen3-1.7b' },
  ],
  knowledge: [{ id: 'procedures', name: 'Procedures' }],
  tools: [
    { id: 'calc', name: '4CE Engineering Calculations' },
    { id: 'files', name: '4CE Workspace Files' },
  ],
  skills: [],
};

const setup = (onsave = vi.fn(async () => {})) => ({
  onsave,
  ...render(ModelEditor, { props: { ...lists, onsave } }),
});

describe('model editor (workspace F34 to F54)', () => {
  it('makes the id from the name while creating', async () => {
    const { getByPlaceholderText } = setup();
    await fireEvent.input(getByPlaceholderText('Model Name'), {
      target: { value: 'Ratio Helper' },
    });
    expect((getByPlaceholderText('Model ID') as HTMLInputElement).value).toBe('ratio-helper');
  });

  it('says what is missing instead of saving', async () => {
    const { getByPlaceholderText, getByRole, findByRole, onsave } = setup();
    await fireEvent.input(getByPlaceholderText('Model Name'), {
      target: { value: 'Ratio Helper' },
    });
    await fireEvent.click(getByRole('button', { name: 'Save & Create' }));
    expect((await findByRole('alert')).textContent).toContain('Base Model is required.');
    expect(onsave).not.toHaveBeenCalled();
  });

  it('saves the record once a base model is chosen', async () => {
    const { getByPlaceholderText, getByRole, findByRole, onsave } = setup();
    await fireEvent.input(getByPlaceholderText('Model Name'), {
      target: { value: 'Ratio Helper' },
    });
    await fireEvent.click(getByRole('button', { name: /Select a base model/ }));
    await fireEvent.click(await findByRole('option', { name: /qwen3-1.7b/ }));
    await fireEvent.click(getByRole('button', { name: 'Save & Create' }));
    expect(onsave).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'ratio-helper',
        name: 'Ratio Helper',
        base: 'qwen/qwen3-1.7b',
      }),
    );
  });

  it('shows File Context and Builtin Tools only while their capability is on', async () => {
    const { getByRole, queryByRole, queryByText } = setup();
    expect(queryByRole('checkbox', { name: 'File Context' })).not.toBeNull();
    await fireEvent.click(getByRole('checkbox', { name: 'File Upload' }));
    expect(queryByRole('checkbox', { name: 'File Context' })).toBeNull();
    expect(queryByText('Time & Calculation')).not.toBeNull();
    await fireEvent.click(getByRole('checkbox', { name: 'Builtin Tools' }));
    expect(queryByText('Time & Calculation')).toBeNull();
  });

  it('picks tools from a search list with Enable all', async () => {
    const { getByText, findByText, queryByText } = setup();
    expect(queryByText('Select Skill')).toBeNull();
    await fireEvent.click(getByText('Select Tool'));
    await fireEvent.click(await findByText('Enable all (2)'));
    expect(queryByText('4CE Workspace Files')).not.toBeNull();
    expect(queryByText('Disable all')).not.toBeNull();
  });

  it('adds a blank suggestion when Prompts turns to Custom', async () => {
    const { getByRole, getAllByPlaceholderText } = setup();
    const prompts = getByRole('group', { name: 'Prompts' });
    await fireEvent.click(within(prompts).getByRole('button', { name: 'Default' }));
    expect(getAllByPlaceholderText('Title')).toHaveLength(1);
  });
});
