import { describe, expect, it } from 'vitest';
import { deriveRun, formatStageTime, RAIL, stageDetails } from './stages';
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

describe('stageDetails', () => {
  const tool = (at: number, state: 'running' | 'done', output?: string): StreamEvent => ({
    type: 'tool',
    at,
    call: { id: 't1', name: 'knowledge_search', input: 'R2', output, state },
  });
  const source = (at: number, index: number, title: string): StreamEvent => ({
    type: 'source',
    at,
    source: { index, title, passage: '' },
  });
  const delta = (at: number, text: string): StreamEvent => ({ type: 'delta', at, text });

  it("gives each node what it did, the Reader's search inside the Analyst's stage", () => {
    const details = stageDetails([
      s(1000, 'planner', 'Planner: reading the request'),
      s(2000, 'reader', 'Reader: searching the knowledge base'),
      tool(2300, 'running'),
      tool(3200, 'done', '2 passages'),
      source(3300, 1, 'Rule R2 · Ratio'),
      source(3400, 2, 'CASE-0142 second batch report'),
      s(4000, 'analyst', 'Analyst: comparing the reading with the limit'),
      s(6600, 'author', 'Author: drafting the answer'),
      delta(7000, 'Yes. '),
      delta(7100, 'Within the limit.'),
      s(7600, 'challenger', 'Challenger: checking every figure'),
      s(10_000, 'challenger', 'Challenger: pass, every figure is supported'),
      s(10_300, 'sign-off', 'Waiting for sign-off'),
    ]);
    expect(details.planner.lines).toEqual([
      { ms: 0, role: 'planner', text: 'Planner: reading the request', try: 1 },
    ]);
    expect(details.analyst.lines.map((line) => [line.ms, line.role])).toEqual([
      [1000, 'reader'],
      [3000, 'analyst'],
    ]);
    expect(details.analyst.calls).toEqual([
      { id: 't1', name: 'knowledge_search', input: 'R2', output: '2 passages', state: 'done' },
    ]);
    expect(details.analyst.sources.map((item) => item.index)).toEqual([1, 2]);
    expect(details.author.text).toBe('Yes. Within the limit.');
    expect(details.challenger.lines).toHaveLength(2);
    expect(details['sign-off'].lines.map((line) => line.text)).toEqual(['Waiting for sign-off']);
  });

  it("marks a second try's lines and gives the Challenger the replan line", () => {
    const details = stageDetails([
      s(0, 'planner'),
      s(1000, 'analyst', 'Analyst: a first look'),
      s(2000, 'author'),
      s(3000, 'challenger', 'Challenger: fail, the ratio is rounded'),
      s(3600, 'replan', 'Replanned, with the objections attached'),
      s(4100, 'analyst', 'Analyst: checking the exact reading'),
      s(5900, 'author'),
      delta(6000, 'Exact.'),
      s(6500, 'challenger', 'Challenger: pass'),
    ]);
    expect(details.analyst.lines.map((line) => line.try)).toEqual([1, 2]);
    expect(details.author.lines.map((line) => line.try)).toEqual([1, 2]);
    expect(details.challenger.lines.map((line) => [line.role, line.try])).toEqual([
      ['challenger', 1],
      ['replan', 1],
      ['challenger', 2],
    ]);
    expect(details.author.text).toBe('Exact.');
  });
});
