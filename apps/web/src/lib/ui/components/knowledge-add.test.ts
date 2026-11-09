import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import KnowledgeDetail from './KnowledgeDetail.svelte';

const setup = async () => {
  const source = createFakeSource({ pace: 0 });
  const base = (await source.getKnowledge('plant-notes-1'))!;
  const view = render(KnowledgeDetail, { props: { base, source } });
  await view.findByText('MEC-014_notes.txt');
  return { source, ...view };
};

// Opens the Add Content menu and picks an item.
const choose = async (view: Awaited<ReturnType<typeof setup>>, item: string) => {
  const add = view.getByRole('button', { name: 'Add Content' });
  await fireEvent.pointerDown(add, { button: 0, pointerType: 'mouse' });
  await fireEvent.click(await view.findByRole('menuitem', { name: item }));
};

describe('adding to a knowledge base (workspace F71, F76, F78, F82, F83)', () => {
  it('creates a folder, and asks for a name first', async () => {
    const view = await setup();
    await choose(view, 'New directory');
    await fireEvent.click(view.getByRole('button', { name: 'Create' }));
    expect((await view.findByRole('alert')).textContent).toContain('Name is required.');
    await fireEvent.input(view.getByPlaceholderText('Directory name'), {
      target: { value: 'Readings' },
    });
    await fireEvent.click(view.getByRole('button', { name: 'Create' }));
    expect(await view.findByText('Readings')).toBeTruthy();
  });

  it('adds typed text as a document named after its title', async () => {
    const view = await setup();
    await choose(view, 'Add text content');
    await fireEvent.input(view.getByPlaceholderText('Title'), { target: { value: 'Shift notes' } });
    await fireEvent.input(view.getByPlaceholderText('Write something...'), {
      target: { value: 'Unit 101B ran warm.' },
    });
    await fireEvent.click(view.getByRole('button', { name: 'Save' }));
    expect(await view.findByText('Shift notes.txt')).toBeTruthy();
  });

  it('uploads files and refuses empty ones', async () => {
    const view = await setup();
    const input = view.container.querySelector<HTMLInputElement>(
      'input[type="file"]:not([webkitdirectory])',
    )!;
    const files = [new File(['Readings.'], 'week-1.txt'), new File([], 'empty.txt')];
    Object.defineProperty(input, 'files', { value: files });
    await fireEvent.change(input);
    expect(await view.findByText('week-1.txt')).toBeTruthy();
    expect((await view.findByRole('alert')).textContent).toContain('Cannot upload an empty file.');
    expect(view.queryByText('empty.txt')).toBeNull();
  });

  it('resets the base after asking', async () => {
    const view = await setup();
    await choose(view, 'Reset');
    expect(view.getByText('Reset knowledge base?')).toBeTruthy();
    await fireEvent.click(view.getByRole('button', { name: 'Confirm' }));
    expect(await view.findByText('No content found')).toBeTruthy();
  });

  it('deletes a folder but keeps its contents when asked to', async () => {
    const source = createFakeSource({ pace: 0 });
    const folder = await source.createFolder('plant-notes-1', 'Old');
    await source.addDocument('plant-notes-1', {
      name: 'kept.txt',
      text: 'Kept.',
      folder: folder.id,
    });
    const base = (await source.getKnowledge('plant-notes-1'))!;
    const view = render(KnowledgeDetail, { props: { base, source } });
    await view.findByText('Old');
    const more = view.getAllByRole('button', { name: 'More' })[0];
    await fireEvent.pointerDown(more, { button: 0, pointerType: 'mouse' });
    await fireEvent.click(await view.findByRole('menuitem', { name: 'Delete' }));
    await fireEvent.click(
      view.getByRole('checkbox', { name: 'Delete all contents inside this directory' }),
    );
    await fireEvent.click(view.getByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(view.queryByText('Old')).toBeNull());
    expect(await view.findByText('kept.txt')).toBeTruthy();
  });
});
