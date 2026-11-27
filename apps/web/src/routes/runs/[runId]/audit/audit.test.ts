import { render } from '@testing-library/svelte';
import { tick } from 'svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { formatDateTime } from '$lib/ui/format';
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

  it('stamps the time it is printed, not the time it was opened', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    const opened = new Date('2026-11-27T05:00:00Z');
    const later = new Date('2026-11-27T07:30:00Z');
    vi.setSystemTime(opened);
    const decided = {
      id: 'run-1',
      chatId: 'c-1',
      question: 'Is R2 within the limit?',
      finished: true,
      events: [
        {
          type: 'decision' as const,
          at: opened.getTime(),
          outcome: 'released' as const,
          by: 'Asha Rao',
          seq: 1,
        },
        { type: 'done' as const, at: opened.getTime(), seq: 2 },
      ],
    };
    const { container } = render(Page, {
      props: { data: { run: decided, user: undefined, chats: [] }, params: { runId: 'run-1' } },
    });
    const footer = () => container.querySelector('footer')?.textContent ?? '';
    expect(footer()).toContain(`Printed ${formatDateTime(opened)}`);
    vi.setSystemTime(later);
    window.dispatchEvent(new Event('beforeprint'));
    await tick();
    expect(footer()).toContain(`Printed ${formatDateTime(later)}`);
  });
});

afterEach(() => vi.useRealTimers());
