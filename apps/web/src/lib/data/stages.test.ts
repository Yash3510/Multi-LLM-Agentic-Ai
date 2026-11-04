import { describe, expect, it } from 'vitest';
import { deriveRun, formatStageTime, RAIL } from './stages';
import type { Role, StreamEvent } from './types';

const s = (at: number, stage: Role | 'replan', description = ''): StreamEvent => ({
  type: 'status',
  at,
  stage,
  description,
});

describe('formatStageTime', () => {
  it('uses <0.1s, one decimal under a minute, then minutes and padded seconds', () => {
    expect(formatStageTime(40)).toBe('<0.1s');
    expect(formatStageTime(3700)).toBe('3.7s');
    expect(formatStageTime(59_960)).toBe('1m 00s');
    expect(formatStageTime(65_000)).toBe('1m 05s');
  });
});

describe('deriveRun', () => {
  it('draws no rail for a direct reply', () => {
    const run = deriveRun([s(0, 'planner', 'Classifying'), { type: 'done', at: 500 }], true, 500);
    expect(run.rail).toBe(false);
  });

  it('gives each stage its time and marks the frontier active while live', () => {
    const run = deriveRun([s(0, 'planner'), s(1000, 'analyst'), s(4700, 'author')], false, 6000);
    expect(run.rail).toBe(true);
    expect(run.stages.planner).toMatchObject({ state: 'done', ms: 1000 });
    expect(run.stages.analyst).toMatchObject({ state: 'done', ms: 3700 });
    expect(run.stages.author).toMatchObject({ state: 'active', ms: 1300 });
    expect(run.stages.challenger.state).toBe('pending');
    expect(run.stages['sign-off'].state).toBe('pending');
  });

  it('counts passes after a re-plan and requeues the agents that must run again', () => {
    const run = deriveRun(
      [
        s(0, 'planner'),
        s(100, 'analyst'),
        s(200, 'author'),
        s(300, 'challenger', 'Challenger: fail, a figure is unsupported'),
        s(400, 'replan'),
        s(500, 'analyst'),
      ],
      false,
      600,
    );
    expect(run.replans).toBe(1);
    expect(run.stages.analyst).toMatchObject({ state: 'active', passes: 2 });
    expect(run.stages.author.state).toBe('requeued');
    expect(run.stages.challenger.state).toBe('requeued');
  });

  it('ends released when the run finishes after the sign-off, and sums the agents only', () => {
    const run = deriveRun(
      [
        s(0, 'planner'),
        s(1000, 'analyst'),
        s(2000, 'author'),
        s(3000, 'challenger', 'Challenger: pass'),
        s(4000, 'sign-off', 'Waiting for sign-off'),
        { type: 'decision', at: 9000, outcome: 'released', by: 'A. Rao' },
        { type: 'done', at: 9000 },
      ],
      true,
      9000,
    );
    expect(run.stages['sign-off']).toMatchObject({ state: 'released', note: 'released' });
    expect(run.stages.challenger.state).toBe('done');
    expect(run.workingMs).toBe(4000);
  });

  it('marks a failing challenger and a cut-off run', () => {
    const failed = deriveRun(
      [
        s(0, 'planner'),
        s(10, 'analyst'),
        s(20, 'author'),
        s(30, 'challenger', 'fail'),
        s(40, 'author'),
      ],
      false,
      50,
    );
    expect(failed.stages.challenger.state).toBe('fail');

    const cut = deriveRun([s(0, 'planner'), s(10, 'analyst')], true, 50);
    expect(cut.stages.analyst).toMatchObject({ state: 'interrupted', note: 'interrupted' });
    expect(cut.stages.author.state).toBe('skipped');
  });

  it('draws the five rail stages in order, without Reader', () => {
    expect(RAIL).toEqual(['planner', 'analyst', 'author', 'challenger', 'sign-off']);
  });
});
