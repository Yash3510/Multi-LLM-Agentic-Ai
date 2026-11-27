import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import EvidenceViewer from './EvidenceViewer.svelte';

const box = { x: 0.3, y: 0.2, width: 0.25, height: 0.05 };
const evidence = {
  id: 'ev-1',
  name: 'CASE-0142 second batch report',
  kind: 'Batch report',
  pages: [{ image: 'data:image/svg+xml,%3Csvg%2F%3E', width: 600, height: 800 }],
  reader: 'qwen/qwen3-8b',
  observations: [
    { id: 'ob-1', index: 1, page: 1, box, label: 'Batch', value: 'Second', confidence: 1 },
    {
      id: 'ob-2',
      index: 2,
      page: 1,
      box,
      label: 'Ratio',
      value: '82.5',
      unit: '%',
      confidence: 0.86,
    },
  ],
};

describe('EvidenceViewer', () => {
  it('keeps the selected box and its row in step, either way', async () => {
    const { getByRole } = render(EvidenceViewer, { props: { evidence } });
    const box2 = getByRole('button', { name: 'Box 2: Ratio, 82.5 %' });
    const row1 = getByRole('button', { name: /^1 Batch/ });
    await fireEvent.click(box2);
    expect(getByRole('button', { name: /^2 Ratio/ }).getAttribute('aria-pressed')).toBe('true');
    await fireEvent.click(row1);
    expect(getByRole('button', { name: 'Box 1: Batch, Second' }).getAttribute('aria-pressed')).toBe(
      'true',
    );
    expect(box2.getAttribute('aria-pressed')).toBe('false');
  });

  it('asks for a check on what was read with less than full confidence, and opens on a box', () => {
    const { getByRole } = render(EvidenceViewer, { props: { evidence, box: 2 } });
    expect(getByRole('button', { name: /^2 Ratio/ }).textContent).toContain('check');
    expect(getByRole('button', { name: /^1 Batch/ }).textContent).not.toContain('check');
    expect(getByRole('button', { name: 'Box 2: Ratio, 82.5 %' }).getAttribute('aria-pressed')).toBe(
      'true',
    );
  });
});
