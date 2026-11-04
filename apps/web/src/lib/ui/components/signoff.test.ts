import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ReceiptStrip from './ReceiptStrip.svelte';
import SignOffPanel from './SignOffPanel.svelte';

const request = {
  checks: [
    { label: 'R2 · Ratio within its limit', verdict: 'pass' as const },
    { label: 'Every figure has a source', verdict: 'pass' as const },
  ],
};
const sources = [
  { index: 1, title: 'Rule R2 · Ratio', passage: 'The ratio shall not exceed 85 %.' },
];

describe('SignOffPanel', () => {
  it('releases only once the person types approve', async () => {
    const ondecide = vi.fn();
    const { getByRole } = render(SignOffPanel, {
      props: { request, draft: 'Yes [1].', sources, model: 'qwen/qwen3-8b', ondecide },
    });
    expect(getByRole('region', { name: 'Review before release' })).toBeTruthy();
    const approve = getByRole('button', { name: 'Approve' });
    await fireEvent.click(approve);
    expect(ondecide).not.toHaveBeenCalled();
    await fireEvent.input(getByRole('textbox'), { target: { value: 'approve' } });
    await fireEvent.click(approve);
    expect(ondecide).toHaveBeenCalledWith('released');
  });

  it('withholds on Withhold and keeps Esc as a no', async () => {
    const ondecide = vi.fn();
    const { getByRole } = render(SignOffPanel, {
      props: { request, draft: 'Yes.', sources, model: 'qwen/qwen3-8b', ondecide },
    });
    await fireEvent.keyDown(getByRole('textbox'), { key: 'Escape' });
    expect(ondecide).not.toHaveBeenCalled();
    await fireEvent.click(getByRole('button', { name: 'Withhold' }));
    expect(ondecide).toHaveBeenCalledWith('withheld');
  });

  it('shows the verdict and what was checked', () => {
    const { getByText } = render(SignOffPanel, {
      props: { request, draft: 'Yes.', sources, model: 'qwen/qwen3-8b', ondecide: vi.fn() },
    });
    expect(getByText('Passed by Challenger')).toBeTruthy();
    expect(getByText('Every figure has a source')).toBeTruthy();
  });
});

describe('ReceiptStrip', () => {
  const receipt = {
    fingerprint: '3f9a21c0b7e4d815',
    model: 'qwen/qwen3-8b',
    seconds: 9.4,
    sources: 2,
    signedBy: 'Asha Rao',
    externalCalls: 0,
    folds: [
      { title: 'Full provenance', body: '| Figure | Source |\n| --- | --- |\n| 82.5 % | [2] |' },
    ],
  };

  it('labels how the answer was produced in the running app order', () => {
    const { getByRole, container } = render(ReceiptStrip, {
      props: {
        receipt,
        checks: request.checks,
        releasedAt: new Date(2026, 10, 4, 14, 5),
        cited: ['Rule R2 · Ratio'],
      },
    });
    expect(getByRole('group', { name: 'How this answer was produced' })).toBeTruthy();
    const labels = [...container.querySelectorAll('.label')].map((label) =>
      label.textContent?.replace(/\s+/g, ' ').trim(),
    );
    expect(labels).toEqual([
      'Local qwen/qwen3-8b',
      'Grounded 2 sources',
      'Checked Challenger passed it',
      'Released by Asha Rao, 14:05',
      '9s working',
      '0 external calls, observed',
      'Fingerprint 3f9a21c0',
      'Audit',
    ]);
    expect(container.querySelector('[data-label="grounded"]')?.getAttribute('title')).toBe(
      'Cited: Rule R2 · Ratio',
    );
  });

  it('counts reservations in amber', () => {
    const { container } = render(ReceiptStrip, {
      props: {
        receipt,
        checks: [...request.checks, { label: 'A figure is rounded', verdict: 'review' as const }],
      },
    });
    const checked = container.querySelector('[data-label="checked"]');
    expect(checked?.textContent?.replace(/\s+/g, ' ').trim()).toBe(
      'Checked Challenger passed it, 1 reservation',
    );
    expect(checked?.getAttribute('data-tone')).toBe('warn');
  });

  it('folds provenance and the execution timeline', async () => {
    const { getByRole, container } = render(ReceiptStrip, {
      props: {
        receipt,
        checks: request.checks,
        timeline: [{ at: '+0.0s', text: 'Planner: reading the request' }],
      },
    });
    expect(container.querySelector('table')).toBeNull();
    await fireEvent.click(getByRole('button', { name: 'Full provenance' }));
    expect(container.querySelector('table')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Execution timeline' }));
    expect(container.textContent).toContain('Planner: reading the request');
  });
});
