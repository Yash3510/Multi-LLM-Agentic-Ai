import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import RunErrorCard from './RunErrorCard.svelte';

describe('RunErrorCard', () => {
  it('says what went wrong, retries once and shows the server detail', async () => {
    const onretry = vi.fn();
    const { getByRole, getByText, queryByText } = render(RunErrorCard, {
      props: { detail: 'All connection attempts failed', role: 'Analyst', onretry },
    });
    expect(getByRole('heading', { name: "The model server isn't running" })).toBeTruthy();
    expect(getByText('Open Bionic.')).toBeTruthy();
    const retry = getByRole('button', { name: 'Try again' });
    await fireEvent.click(retry);
    expect(onretry).toHaveBeenCalledOnce();
    expect(retry.textContent?.trim()).toBe('Trying again');
    expect(retry.hasAttribute('disabled')).toBe(true);
    expect(queryByText('All connection attempts failed')).toBeNull();
    await fireEvent.click(getByRole('button', { name: 'What the server said' }));
    expect(getByText('All connection attempts failed')).toBeTruthy();
  });

  it('hides Try again when retrying is not allowed', () => {
    const { queryByRole } = render(RunErrorCard, { props: { detail: 'boom' } });
    expect(queryByRole('button', { name: 'Try again' })).toBeNull();
  });
});
