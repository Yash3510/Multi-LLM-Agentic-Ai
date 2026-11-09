import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import CreateKnowledgeDialog from './CreateKnowledgeDialog.svelte';
import KnowledgeList from './KnowledgeList.svelte';

const day = 86_400_000;
const bases = [
  {
    id: 'a',
    name: 'Plant Notes',
    description: 'Reference readings.',
    updated: new Date(Date.now() - 60 * day),
    owner: { name: '4CE Administrator' },
    files: 2,
    writable: true,
    source: 'local' as const,
  },
  {
    id: 'b',
    name: 'Ratio Notes',
    description: 'Ratios.',
    updated: new Date(Date.now() - 2 * day),
    files: 0,
    writable: false,
    source: 'local' as const,
  },
];

describe('knowledge list (workspace F57 to F64)', () => {
  it('shows each base with its age, summary and owner', () => {
    const { getByText, getAllByText } = render(KnowledgeList, { props: { bases } });
    expect(getByText('2 months ago')).toBeTruthy();
    expect(getByText('2 files · Reference readings.')).toBeTruthy();
    expect(getByText('4CE Administrator')).toBeTruthy();
    expect(getAllByText('Read Only')).toHaveLength(1);
  });

  it('filters by the search text and says when nothing matches', async () => {
    const { getByPlaceholderText, queryByText, getByText } = render(KnowledgeList, {
      props: { bases },
    });
    await fireEvent.input(getByPlaceholderText('Search Knowledge'), { target: { value: 'ratio' } });
    expect(queryByText('Plant Notes')).toBeNull();
    await fireEvent.input(getByPlaceholderText('Search Knowledge'), { target: { value: 'zzz' } });
    expect(getByText('No knowledge found')).toBeTruthy();
  });

  it('opens a base from its row', async () => {
    const onopen = vi.fn();
    const { getByText } = render(KnowledgeList, { props: { bases, onopen } });
    await fireEvent.click(getByText('Plant Notes'));
    expect(onopen).toHaveBeenCalledWith('a');
  });
});

describe('create knowledge dialog (F65)', () => {
  it('keeps what was typed when a field is missing', async () => {
    const oncreate = vi.fn(async () => {});
    const { getByPlaceholderText, getByRole, findByRole } = render(CreateKnowledgeDialog, {
      props: { open: true, oncreate, onclose: () => {} },
    });
    const name = getByPlaceholderText('Name your knowledge base') as HTMLInputElement;
    await fireEvent.input(name, { target: { value: 'Ratio notes' } });
    await fireEvent.click(getByRole('button', { name: 'Create Knowledge' }));
    expect((await findByRole('alert')).textContent).toContain('Please fill in all fields.');
    expect(name.value).toBe('Ratio notes');
    expect(oncreate).not.toHaveBeenCalled();
  });

  it('creates with both fields filled', async () => {
    const oncreate = vi.fn(async () => {});
    const { getByPlaceholderText, getByRole } = render(CreateKnowledgeDialog, {
      props: { open: true, oncreate, onclose: () => {} },
    });
    await fireEvent.input(getByPlaceholderText('Name your knowledge base'), {
      target: { value: 'Ratio notes' },
    });
    await fireEvent.input(getByPlaceholderText('Describe your knowledge base and objectives'), {
      target: { value: 'Ratios to check.' },
    });
    await fireEvent.click(getByRole('button', { name: 'Create Knowledge' }));
    expect(oncreate).toHaveBeenCalledWith('Ratio notes', 'Ratios to check.');
  });
});
