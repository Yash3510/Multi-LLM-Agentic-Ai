import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import KnowledgeDetail from './KnowledgeDetail.svelte';

const setup = async () => {
  const source = createFakeSource({ pace: 0 });
  const base = (await source.getKnowledge('plant-notes-1'))!;
  return { source, ...render(KnowledgeDetail, { props: { base, source } }) };
};

afterEach(() => vi.useRealTimers());

describe('knowledge detail (workspace F66 to F77)', () => {
  it('shows the base, its file count, id and documents', async () => {
    const { findByText, getByText, getAllByText, getByDisplayValue } = await setup();
    expect(getByDisplayValue('Plant Notes')).toBeTruthy();
    expect(getByText('plant-notes-1')).toBeTruthy();
    expect(await findByText('MEC-014_notes.txt')).toBeTruthy();
    expect(getByText('2 files')).toBeTruthy();
    expect(getByText('2.0 KB')).toBeTruthy();
    expect(getAllByText('By 4CE Administrator')).toHaveLength(2);
  });

  it('saves the name a second after typing stops, and refuses an empty one', async () => {
    const { source, getByDisplayValue, findByRole } = await setup();
    const save = vi.spyOn(source, 'updateKnowledge');
    vi.useFakeTimers();
    const name = getByDisplayValue('Plant Notes');
    await fireEvent.input(name, { target: { value: 'Unit notes' } });
    await vi.advanceTimersByTimeAsync(1000);
    expect(save).toHaveBeenCalledWith('plant-notes-1', {
      name: 'Unit notes',
      description: expect.any(String),
    });
    await fireEvent.input(name, { target: { value: ' ' } });
    await vi.advanceTimersByTimeAsync(1000);
    vi.useRealTimers();
    expect((await findByRole('alert')).textContent).toContain('Please fill in all fields.');
    expect(save).toHaveBeenCalledTimes(1);
  });

  it('opens a document and saves its text', async () => {
    const { source, findByText, findByDisplayValue, getByRole } = await setup();
    await fireEvent.click(await findByText('MEC-014_notes.txt'));
    const text = await findByDisplayValue('Notes on the unit 101B readings.');
    await fireEvent.input(text, { target: { value: 'Edited.' } });
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () => expect(await source.getDocumentText('doc-2')).toBe('Edited.'));
  });

  it('searches the collection', async () => {
    const { findByText, getByPlaceholderText, queryByText } = await setup();
    await findByText('MEC-014_notes.txt');
    await fireEvent.input(getByPlaceholderText('Search Collection'), {
      target: { value: 'readings_unit' },
    });
    await waitFor(() => expect(queryByText('MEC-014_notes.txt')).toBeNull());
  });

  it('opens a folder and shows the path back to the base', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.createFolder('plant-notes-1', 'Readings');
    const base = (await source.getKnowledge('plant-notes-1'))!;
    const { findByText, getByRole } = render(KnowledgeDetail, { props: { base, source } });
    await fireEvent.click(await findByText('Readings'));
    const crumbs = getByRole('navigation', { name: 'Breadcrumb' });
    await waitFor(() => expect(crumbs.textContent).toContain('Plant Notes'));
    expect(await findByText('No content found')).toBeTruthy();
  });
});
