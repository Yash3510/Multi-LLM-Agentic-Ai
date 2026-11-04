import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import type { Role, StreamEvent } from '$lib/data';
import StageRail from './StageRail.svelte';

const status = (at: number, stage: Role): StreamEvent => ({
  type: 'status',
  at,
  stage,
  description: '',
});

const finishedRun: StreamEvent[] = [
  status(0, 'planner'),
  status(1000, 'analyst'),
  status(4700, 'author'),
  status(6000, 'challenger'),
  status(7000, 'sign-off'),
  { type: 'decision', at: 12_000, outcome: 'released', by: 'A. Rao' },
  { type: 'done', at: 12_000 },
];

describe('StageRail', () => {
  it('is an agent-chain list of the five nodes, the gate shown as YOU', () => {
    const { getByRole, getAllByRole } = render(StageRail, {
      props: { events: finishedRun, finished: true },
    });
    expect(getByRole('list', { name: 'Agent chain' })).toBeTruthy();
    expect(
      getAllByRole('listitem').map((item) => item.querySelector('.name')?.textContent?.trim()),
    ).toEqual(['PLANNER', 'ANALYST', 'AUTHOR', 'CHALLENGER', 'YOU']);
  });

  it('shows each stage time and the person waiting at sign-off', () => {
    const { container } = render(StageRail, { props: { events: finishedRun, finished: true } });
    const times = [...container.querySelectorAll('.time')].map((line) => line.textContent?.trim());
    expect(times).toEqual(['1.0s', '3.7s', '1.3s', '1.0s', 'waited 5.0s']);
    expect(container.querySelector('[data-stage="sign-off"] .note')?.textContent).toBe('released');
  });

  it('keeps nodes disabled while the run is live', () => {
    const { getAllByRole } = render(StageRail, {
      props: { events: finishedRun.slice(0, 3), finished: false, now: 5000 },
    });
    expect(getAllByRole('button').every((button) => button.hasAttribute('disabled'))).toBe(true);
  });

  it('draws nothing for a direct reply', () => {
    const { container } = render(StageRail, {
      props: { events: [status(0, 'planner'), { type: 'done', at: 10 }], finished: true },
    });
    expect(container.querySelector('[role="list"]')).toBeNull();
  });
});
