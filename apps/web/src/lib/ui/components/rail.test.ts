import { render } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
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

describe('StageRail pacing', () => {
  afterEach(() => vi.useRealTimers());
  const stateOf = (container: HTMLElement, stage: string) =>
    container.querySelector(`[data-stage="${stage}"]`)?.getAttribute('data-state');

  it('starts at the frontier on first sight, without replaying', () => {
    const { container } = render(StageRail, {
      props: { events: finishedRun.slice(0, 3), finished: false, now: 5000, paced: true },
    });
    expect(stateOf(container, 'author')).toBe('active');
  });

  it('trails the run one hop at a time and says who it is passing to', async () => {
    vi.useFakeTimers();
    const onhandover = vi.fn();
    const view = render(StageRail, {
      props: {
        events: finishedRun.slice(0, 2),
        finished: false,
        now: 2000,
        paced: true,
        onhandover,
      },
    });
    expect(stateOf(view.container, 'analyst')).toBe('active');
    await view.rerender({
      events: finishedRun.slice(0, 3),
      finished: false,
      now: 5000,
      paced: true,
      onhandover,
    });
    // The Analyst closes, then the light travels; the Author still looks unreached.
    expect(stateOf(view.container, 'author')).toBe('pending');
    await vi.advanceTimersByTimeAsync(1000);
    expect(onhandover).toHaveBeenLastCalledWith('author');
    expect(
      view.container.querySelector('[data-stage="analyst"] [data-wire="travel"]'),
    ).toBeTruthy();
    await vi.advanceTimersByTimeAsync(2000);
    expect(stateOf(view.container, 'author')).toBe('active');
    expect(onhandover).toHaveBeenLastCalledWith(undefined);
  });
});

describe('StageRail re-plan spark', () => {
  it('sends a spark along the arc once per re-plan on a live run only', async () => {
    const live: StreamEvent[] = [
      status(0, 'planner'),
      status(100, 'analyst'),
      status(200, 'author'),
      { type: 'status', at: 300, stage: 'challenger', description: 'fail' },
    ];
    const view = render(StageRail, { props: { events: live, finished: false, now: 400 } });
    expect(view.container.querySelector('.spark')).toBeNull();
    await view.rerender({
      events: [...live, { type: 'status', at: 400, stage: 'replan', description: '' }],
      finished: false,
      now: 500,
    });
    expect(view.container.querySelector('.spark')).toBeTruthy();

    const opened = render(StageRail, {
      props: {
        events: [
          ...live,
          { type: 'status', at: 400, stage: 'replan', description: '' },
          { type: 'done', at: 600 },
        ],
        finished: true,
      },
    });
    expect(opened.container.querySelector('.spark')).toBeNull();
  });
});
