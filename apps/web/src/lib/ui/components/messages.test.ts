import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import ResponseMessage from './ResponseMessage.svelte';
import UserMessage from './UserMessage.svelte';

const at = new Date(2026, 10, 4, 9, 41);

describe('UserMessage', () => {
  it('shows the text in a bubble with its time and the edit, copy and delete actions', () => {
    const { getByText, getByRole, container } = render(UserMessage, {
      text: 'Is R2 within the limit for CASE-0142?',
      at,
    });
    expect(getByText('Is R2 within the limit for CASE-0142?')).toBeTruthy();
    expect(container.querySelector('time')?.getAttribute('datetime')).toBe(at.toISOString());
    for (const name of ['Edit', 'Copy', 'Delete'])
      expect(getByRole('button', { name })).toBeTruthy();
  });
});

describe('ResponseMessage', () => {
  it('names the agent and keeps each paragraph of the answer', () => {
    const { getByText, container } = render(ResponseMessage, {
      model: 'Planner',
      text: 'R2 · Ratio is 82.5 %.\n\nThe limit is 85 %, so it passes.',
      at,
    });
    expect(getByText('Planner')).toBeTruthy();
    expect(container.querySelectorAll('.body p')).toHaveLength(2);
    expect(container.querySelector('.body script')).toBeNull();
  });

  it('offers copy, regenerate and feedback on the answer', () => {
    const { getByRole } = render(ResponseMessage, { model: 'Planner', text: 'Done.', at });
    for (const name of ['Copy', 'Regenerate', 'Good Response', 'Bad Response'])
      expect(getByRole('button', { name })).toBeTruthy();
  });
});
