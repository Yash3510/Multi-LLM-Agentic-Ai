import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import AuditDialog from './AuditDialog.svelte';

const props = {
  open: true,
  outcome: 'released' as const,
  tries: 1,
  externalCalls: 0,
  working: '9.4s',
  at: new Date(2026, 10, 4, 14, 5),
  chain: [
    { role: 'Planner', text: 'reading the request', time: '1.2s' },
    { role: 'You', text: 'Released it · Asha Rao', time: '', tone: 'ink' as const },
  ],
  evidence: [
    { index: 1, title: 'Rule R2 · Ratio', cited: true },
    { index: 3, title: 'Batch one note', cited: false },
  ],
  fingerprint: 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e',
};

describe('AuditDialog', () => {
  it('sums up the run in four tiles, the chain and the evidence', async () => {
    const { getByRole } = render(AuditDialog, { props });
    const dialog = await waitFor(() => getByRole('dialog', { name: 'Audit record' }));
    const tiles = [...dialog.querySelectorAll('.tile')].map((tile) =>
      tile.textContent?.replace(/\s+/g, ' ').trim(),
    );
    expect(tiles).toEqual(['Outcome Released', 'Tries 1', 'External calls 0', 'Working time 9.4s']);
    expect(dialog.textContent).toContain('PLANNER');
    expect(dialog.textContent).toContain('[1] Rule R2 · Ratio');
    expect(dialog.textContent).toContain('retrieved, not cited');
  });

  it('verifies a pasted copy against the fingerprint', async () => {
    const { getByRole, findByText } = render(AuditDialog, { props });
    const field = await waitFor(() =>
      getByRole('textbox', { name: 'Paste a copy of the answer to check it has not been changed' }),
    );
    await fireEvent.input(field, { target: { value: 'Hello World' } });
    await fireEvent.click(getByRole('button', { name: 'Verify' }));
    expect(await findByText('Matches the released answer.')).toBeTruthy();
    await fireEvent.input(field, { target: { value: 'Hello world' } });
    await fireEvent.click(getByRole('button', { name: 'Verify' }));
    expect(await findByText('Does not match: the text has been changed.')).toBeTruthy();
  });
});
