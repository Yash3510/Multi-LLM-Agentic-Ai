import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import RevisionCard from './RevisionCard.svelte';
import SignOffPanel from './SignOffPanel.svelte';

const revision = {
  try: 2,
  objections: [{ by: 'Challenger', text: 'The ratio is rounded without saying so.' }],
  changes: [
    { removed: 'R2 · Ratio is 83 %.', added: 'R2 · Ratio is 82.5 %, as measured.' },
    { removed: 'It is well within the limit.' },
  ],
};

describe('SignOffPanel on a second try', () => {
  it('shows what changed since try 1 and marks the rewritten block', async () => {
    const { getByRole, container } = render(SignOffPanel, {
      props: {
        request: { checks: [{ label: 'Figures match', verdict: 'pass' as const }], revision },
        draft: 'R2 · Ratio is 82.5 %, as measured.\n\nThe limit is 85 %.',
        sources: [],
        model: 'qwen/qwen3-8b',
        ondecide: vi.fn(),
      },
    });
    const toggle = getByRole('button', { name: 'Show what changed since try 1' });
    expect(toggle.getAttribute('aria-pressed')).toBe('false');
    await fireEvent.click(toggle);
    expect(toggle.getAttribute('aria-pressed')).toBe('true');
    const box = container.querySelector('.changes')!;
    expect(box.textContent).toContain(
      'CHALLENGER on try 1: “The ratio is rounded without saying so.”',
    );
    expect(box.textContent).toContain('Taken out: It is well within the limit.');
    expect(container.querySelector('.draft-text [data-changed]')?.textContent).toContain('82.5 %');
    expect(container.querySelector('.draft-text [data-was]')?.textContent).toBe(
      'R2 · Ratio is 83 %.',
    );
  });
});

describe('RevisionCard', () => {
  it('says what changed on try 2 and that it passed', () => {
    const { getByRole } = render(RevisionCard, { props: { revision, passed: true } });
    const card = getByRole('group', { name: 'What changed on try 2' });
    expect(card.textContent).toContain('Passed on try 2');
    expect(card.textContent).toContain('CHALLENGER · try 1');
    expect(card.textContent).toContain('AUTHOR · try 2');
    expect(card.textContent).toContain('Passed the revised draft.');
  });
});
