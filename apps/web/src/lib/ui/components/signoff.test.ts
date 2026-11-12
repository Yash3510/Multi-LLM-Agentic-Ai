import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ReceiptStrip from './ReceiptStrip.svelte';
import DetailsPanel from './DetailsPanel.svelte';
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

  it('shows provenance, the timeline and the sources as tabs of one panel', async () => {
    const onopen = vi.fn();
    const { getByRole, container } = render(DetailsPanel, {
      props: {
        folds: [
          {
            title: 'Full provenance',
            body: '| Figure | Source |\n| --- | --- |\n| 82.5 % | [1] |',
          },
        ],
        sources,
        checks: request.checks,
        answer: 'Within the limit [1].',
        steps: [
          { ms: 0, stage: 'planner', text: 'Planner: reading the request' },
          { ms: 1200, stage: 'sign-off', text: 'Waiting for sign-off' },
        ],
        onopen,
      },
    });
    expect(getByRole('tab', { name: /Provenance/ }).getAttribute('aria-selected')).toBe('true');
    expect(container.querySelector('table')?.textContent).toContain('82.5 %');
    await fireEvent.click(getByRole('button', { name: /^View source 1:/ }));
    expect(onopen).toHaveBeenCalledWith(1);
    expect(getByRole('tab', { name: /Timeline/ })).toBeTruthy();
    expect(getByRole('tab', { name: /Sources/ })).toBeTruthy();
    expect(container.querySelector('[role="tab"][data-value="reasoning"]')).toBeNull();
  });
});

describe('SignOffPanel draft links', () => {
  const linked = {
    checks: [{ label: 'Measured ratio', verdict: 'pass' as const, cites: [1] }],
  };

  it('highlights the blocks a check rests on while it is hovered', async () => {
    const { getByText, container } = render(SignOffPanel, {
      props: {
        request: linked,
        draft: 'Within the limit [1].\n\nNo other figures.',
        sources,
        model: 'm',
        ondecide: vi.fn(),
      },
    });
    const row = getByText('Measured ratio').closest('li')!;
    await fireEvent.mouseEnter(row);
    expect(container.querySelectorAll('.draft-text [data-hl]')).toHaveLength(1);
    await fireEvent.mouseLeave(row);
    expect(container.querySelectorAll('.draft-text [data-hl]')).toHaveLength(0);
  });

  it('opens the passage under the block when a draft chip is pressed', async () => {
    const { container } = render(SignOffPanel, {
      props: {
        request: linked,
        draft: 'Within the limit [1].',
        sources,
        model: 'm',
        ondecide: vi.fn(),
      },
    });
    await fireEvent.click(container.querySelector('.draft-text .chip')!);
    const card = container.querySelector('.draft-text .passage-card');
    expect(card?.textContent).toContain('Rule R2 · Ratio');
    expect(card?.textContent).toContain('The ratio shall not exceed 85 %.');
    await fireEvent.click(container.querySelector('.draft-text .chip')!);
    expect(container.querySelector('.draft-text .passage-card')).toBeNull();
  });
});
