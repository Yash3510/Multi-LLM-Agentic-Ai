import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import NoteList from './NoteList.svelte';
import NoteEditor from './NoteEditor.svelte';

describe('notes list (notes look §1)', () => {
  it('shows the empty state', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByText } = render(NoteList, { props: { source } });
    expect(await findByText('No Notes')).toBeTruthy();
  });

  it('lists notes under Today, switches to grid, and deletes with Undo', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.createNote({ title: 'Weekly review', content: 'Item 3 needs a second look.' });
    const { findByText, getByRole, findByRole, queryByText } = render(NoteList, {
      props: { source },
    });
    expect(await findByText('Weekly review')).toBeTruthy();
    expect(await findByText('Today')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: /List/ }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Grid' }));
    expect(await findByText('Item 3 needs a second look.')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Note Menu' }));
    await fireEvent.click(await findByRole('menuitem', { name: 'Delete' }));
    await fireEvent.click(await findByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(queryByText('Weekly review')).toBeNull());
    await fireEvent.click(await findByRole('button', { name: 'Undo' }));
    expect(await findByText('Weekly review')).toBeTruthy();
  });
});

describe('note editor (notes look §2)', () => {
  it('saves the text, counts words, and streams an enhanced version', async () => {
    const source = createFakeSource({ pace: 0 });
    const note = await source.createNote({ title: '', content: '' });
    const { getByPlaceholderText, findByText, getByRole } = render(NoteEditor, {
      props: { source, note, ondeleted: vi.fn() },
    });
    await fireEvent.input(getByPlaceholderText('Title'), { target: { value: 'Weekly review' } });
    await fireEvent.input(getByPlaceholderText('Write something...'), {
      target: { value: 'item 3 needs review' },
    });
    expect(await findByText('4 words')).toBeTruthy();
    await waitFor(
      async () => expect((await source.getNote(note.id))?.title).toBe('Weekly review'),
      {
        timeout: 2000,
      },
    );
    await fireEvent.click(getByRole('button', { name: 'Enhance' }));
    await waitFor(() =>
      expect((getByPlaceholderText('Write something...') as HTMLTextAreaElement).value).toBe(
        'Item 3 needs review.',
      ),
    );
  });
});

describe('notes import (notes look §1)', () => {
  it('imports a text file as a note from the Create menu', async () => {
    const source = createFakeSource({ pace: 0 });
    const { getByRole, findByRole, findByText, container } = render(NoteList, {
      props: { source },
    });
    await fireEvent.click(getByRole('button', { name: 'Open create menu' }));
    expect(await findByRole('menuitem', { name: 'Import txt/md' })).toBeTruthy();
    const input = container.ownerDocument.querySelector(
      'input[accept=".txt,.md"]',
    ) as HTMLInputElement;
    await fireEvent.change(input, { target: { files: [new File(['Line one'], 'agenda.md')] } });
    expect(await findByText('agenda')).toBeTruthy();
  });
});
