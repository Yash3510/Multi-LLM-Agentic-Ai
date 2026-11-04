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
  it('labels how the answer was produced, with the short fingerprint', () => {
    const { getByRole, container } = render(ReceiptStrip, {
      props: {
        receipt: {
          fingerprint: '3f9a21c0b7e4d815',
          model: 'qwen/qwen3-8b',
          seconds: 9.4,
          sources: 2,
          signedBy: 'Asha Rao',
        },
        checks: request.checks,
        releasedAt: new Date(2026, 10, 4, 14, 5),
      },
    });
    expect(getByRole('group', { name: 'How this answer was produced' })).toBeTruthy();
    const labels = [...container.querySelectorAll('.label')].map((label) =>
      label.textContent?.replace(/\s+/g, ' ').trim(),
    );
    expect(labels.slice(0, 3)).toEqual([
      'Local qwen/qwen3-8b',
      'Grounded 2 sources',
      'Checked Challenger passed it',
    ]);
    expect(labels[3]).toMatch(/^Released by Asha Rao, /);
    expect(getByRole('button', { name: /Fingerprint/ }).textContent).toContain('3f9a21c0');
  });
});
