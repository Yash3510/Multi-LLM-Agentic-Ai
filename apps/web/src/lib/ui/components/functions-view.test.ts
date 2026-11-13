import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import FunctionList from './FunctionList.svelte';
import FunctionEditor from './FunctionEditor.svelte';

describe('functions list (admin F133 to F155, UI only)', () => {
  it('lists functions with type, version and owner, searches and filters by type', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByText, getByText, getByRole, queryByText } = render(FunctionList, {
      props: { source },
    });
    expect(await findByText('4CE Orchestrator')).toBeTruthy();
    expect(getByText('pipe')).toBeTruthy();
    expect(getByText('v0.1.0')).toBeTruthy();
    expect(getByText('4CE Administrator')).toBeTruthy();
    await fireEvent.input(getByRole('textbox', { name: 'Search Functions' }), {
      target: { value: 'zzz' },
    });
    expect(await findByText('No functions found')).toBeTruthy();
    await fireEvent.input(getByRole('textbox', { name: 'Search Functions' }), {
      target: { value: '' },
    });
    await fireEvent.click(getByRole('button', { name: /Tag/ }));
    await fireEvent.click(await findByText('filter'));
    await waitFor(() => expect(queryByText('4CE Orchestrator')).toBeNull());
  });

  it('says saving waits for the server instead of changing anything', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByText, getByRole } = render(FunctionList, { props: { source } });
    await findByText('4CE Orchestrator');
    await fireEvent.click(getByRole('switch'));
    expect(await findByText(/saved by the 4CE server/)).toBeTruthy();
    expect((await source.listFunctions())[0].enabled).toBe(true);
  });
});

describe('function editor (admin F156 to F168, UI only)', () => {
  it('starts from a 4CE starter and does not save', async () => {
    const source = createFakeSource({ pace: 0 });
    const { getByRole, getByPlaceholderText, findByText } = render(FunctionEditor);
    expect(getByPlaceholderText('Function Name')).toBeTruthy();
    expect((getByRole('combobox', { name: 'Function starter' }) as HTMLSelectElement).value).toBe(
      'filter',
    );
    await fireEvent.click(getByRole('button', { name: 'Save & Create' }));
    expect(await findByText(/saved by the 4CE server/)).toBeTruthy();
    expect(await source.listFunctions()).toHaveLength(1);
  });
});
