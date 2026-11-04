import { render, waitFor } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import CitationDialog from './CitationDialog.svelte';

describe('CitationDialog', () => {
  it('shows the cited passage under the source name', async () => {
    const { getByRole } = render(CitationDialog, {
      props: {
        source: { index: 1, title: 'Rule R2 · Ratio', passage: 'The ratio shall not exceed 85 %.' },
        open: true,
      },
    });
    const dialog = await waitFor(() => getByRole('dialog', { name: 'Rule R2 · Ratio' }));
    expect(dialog.textContent).toContain('Passage');
    expect(dialog.textContent).toContain('The ratio shall not exceed 85 %.');
  });
});
