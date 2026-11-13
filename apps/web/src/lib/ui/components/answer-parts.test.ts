import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import SourcesBar from './SourcesBar.svelte';
import ToolGroup from './ToolGroup.svelte';

describe('ToolGroup', () => {
  it('says the tools are done and folds out each call', async () => {
    const { getByRole, getByText, queryByText } = render(ToolGroup, {
      props: {
        calls: [
          {
            id: 't1',
            name: 'knowledge_search',
            input: 'R2 ratio',
            output: '2 passages',
            state: 'done',
          },
        ],
      },
    });
    const toggle = getByRole('button', { name: 'Toggle details' });
    expect(toggle.dataset.state).toBe('done');
    expect(queryByText('R2 ratio')).toBeNull();
    await fireEvent.click(toggle);
    expect(getByText('R2 ratio')).toBeTruthy();
  });

  it('shows a running state while a call is open', () => {
    const { getByRole } = render(ToolGroup, {
      props: { calls: [{ id: 't1', name: 'knowledge_search', input: 'R2', state: 'running' }] },
    });
    expect(getByRole('button', { name: 'Toggle details' }).dataset.state).toBe('running');
  });
});

describe('SourcesBar', () => {
  it('counts the sources and lists them when opened', async () => {
    const { getByRole, getAllByRole } = render(SourcesBar, {
      props: {
        sources: [
          { index: 1, title: 'Rule R2 · Ratio', passage: '' },
          { index: 2, title: 'CASE-0142 report', passage: '' },
        ],
      },
    });
    const toggle = getByRole('button', { name: 'Toggle 2 sources' });
    expect(toggle.textContent?.trim()).toBe('2 Sources');
    await fireEvent.click(toggle);
    expect(getAllByRole('button', { name: /^View source:/ })).toHaveLength(2);
  });
});
