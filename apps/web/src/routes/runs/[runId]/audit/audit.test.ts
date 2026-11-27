import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Page from './+page.svelte';

describe('the audit sheet', () => {
  it('says a run not yet decided has none, and links to the run', () => {
    const run = { id: 'run-1', chatId: 'c-1', question: 'Is R2 within the limit?', events: [] };
    const { getByText, getByRole, queryByRole } = render(Page, {
      props: {
        data: { run: { ...run, finished: false }, user: undefined, chats: [] },
        params: { runId: 'run-1' },
      },
    });
    expect(getByText(/hasn't been decided yet/)).toBeTruthy();
    expect(getByRole('link', { name: 'Open the run' }).getAttribute('href')).toBe('/runs/run-1');
    expect(queryByRole('article', { name: 'Audit sheet' })).toBeNull();
  });
});
