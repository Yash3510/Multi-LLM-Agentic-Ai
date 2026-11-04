import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import type { Role, StreamEvent } from '$lib/data';
import StatusLine from './StatusLine.svelte';

const status = (at: number, stage: Role, description: string): StreamEvent => ({
  type: 'status',
  at,
  stage,
  description,
});

const run: StreamEvent[] = [
  status(0, 'planner', 'Planner: reading the request'),
  status(1000, 'reader', 'Reader: searching the knowledge base'),
  status(2000, 'analyst', 'Analyst: comparing the reading with the limit'),
  status(4000, 'author', 'Author: drafting the answer'),
];

describe('StatusLine', () => {
  it('opens a live stage on its own description, without the role prefix', () => {
    const { getByRole } = render(StatusLine, { props: { events: run, finished: false } });
    expect(getByRole('button', { name: 'Toggle status history' }).textContent).toContain(
      'Drafting the answer',
    );
  });

  it('sums up a finished run and opens its history', async () => {
    const done: StreamEvent[] = [...run, { type: 'done', at: 5000 }];
    const { getByRole, getAllByRole } = render(StatusLine, {
      props: { events: done, finished: true },
    });
    const toggle = getByRole('button', { name: 'Toggle status history' });
    expect(toggle.textContent?.trim()).toBe('4 steps in 5.0s');
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    await fireEvent.click(toggle);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    expect(getAllByRole('listitem').map((item) => item.textContent?.trim())).toEqual([
      'Planner: reading the request',
      'Reader: searching the knowledge base',
      'Analyst: comparing the reading with the limit',
      'Author: drafting the answer',
    ]);
  });

  it('says how far a stopped run got', () => {
    const { getByRole } = render(StatusLine, {
      props: { events: [...run, { type: 'stopped', at: 4500 }], finished: true },
    });
    expect(getByRole('button', { name: 'Toggle status history' }).textContent?.trim()).toBe(
      'Stopped after 4 steps',
    );
  });
});

describe('StatusLine hand-over', () => {
  it('says who the run is passing to while the light travels', () => {
    const view = render(StatusLine, {
      props: { events: run, finished: false, handover: 'author' },
    });
    expect(view.getByRole('button', { name: 'Toggle status history' }).textContent).toContain(
      'Passing to Author…',
    );
    view.unmount();
    const gate = render(StatusLine, {
      props: { events: run, finished: false, handover: 'sign-off' },
    });
    expect(gate.getByRole('button', { name: 'Toggle status history' }).textContent).toContain(
      'Passing to you for sign-off…',
    );
  });
});
