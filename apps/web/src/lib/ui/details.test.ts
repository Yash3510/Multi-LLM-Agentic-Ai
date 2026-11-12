import { describe, expect, it } from 'vitest';
import { provenanceRows, reasoningSteps, sourceUses, timelineSpans } from './details';

const sources = [
  { index: 1, title: 'Rule R2 · Ratio', passage: 'The ratio must not exceed 85 %.' },
  { index: 2, title: 'CASE-0142 second batch report', passage: 'Measured ratio: 82.5 %.' },
];

describe('provenanceRows', () => {
  it('reads each figure with the sources it cites', () => {
    const body = '| Figure | Source |\n| --- | --- |\n| 82.5 % | [2] |\n| 85 % limit | [1], [2] |';
    expect(provenanceRows(body, sources)).toEqual([
      { figure: '82.5 %', refs: [sources[1]] },
      { figure: '85 % limit', refs: [sources[0], sources[1]] },
    ]);
  });

  it('keeps a citation whose source never arrived, without inventing its text', () => {
    const body = '| Figure | Source |\n| --- | --- |\n| 12 | [7] |';
    expect(provenanceRows(body, sources)).toEqual([{ figure: '12', refs: [{ index: 7 }] }]);
  });

  it('returns nothing for a body that is not a table', () => {
    expect(provenanceRows('No figures in this answer.', sources)).toEqual([]);
  });
});

describe('reasoningSteps', () => {
  it('splits each agent fold into role, step, verdict and model, and leaves provenance out', () => {
    const folds = [
      { title: 'Full provenance', body: '| a | b |' },
      { title: 'Analyst — analysis · qwen/qwen3-8b', body: 'A' },
      { title: 'Challenger — verification — PASS · qwen/qwen3-1.7b', body: 'B' },
    ];
    expect(reasoningSteps(folds)).toEqual([
      { role: 'Analyst', step: 'analysis', model: 'qwen/qwen3-8b', body: 'A' },
      {
        role: 'Challenger',
        step: 'verification',
        verdict: 'PASS',
        model: 'qwen/qwen3-1.7b',
        body: 'B',
      },
    ]);
  });
});

describe('timelineSpans', () => {
  const steps = [
    { ms: 0, stage: 'planner', text: 'Planner: reading the question' },
    { ms: 1200, stage: 'reader', text: 'Reader: searching' },
    { ms: 4000, stage: 'sign-off', text: 'Waiting for sign-off' },
  ];

  it('runs each step until the next one starts, as fractions of the run', () => {
    expect(timelineSpans(steps)).toEqual([
      { at: '+0.0s', role: 'Planner', text: 'reading the question', start: 0, end: 0.3, took: '1.2s' },
      { at: '+1.2s', role: 'Reader', text: 'searching', start: 0.3, end: 1, took: '2.8s' },
      { at: '+4.0s', role: 'Sign-off', text: 'Waiting for sign-off', start: 1, end: 1 },
    ]);
  });

  it('handles a run with one step', () => {
    expect(timelineSpans(steps.slice(0, 1))).toEqual([
      { at: '+0.0s', role: 'Planner', text: 'reading the question', start: 0, end: 0 },
    ]);
  });
});

describe('sourceUses', () => {
  it('says which checks rest on a source and whether the answer cites it', () => {
    const checks = [
      { label: 'R2 within its limit', verdict: 'pass' as const, cites: [1, 2] },
      { label: 'Every figure has a source', verdict: 'pass' as const, cites: [2] },
      { label: 'No cites', verdict: 'review' as const },
    ];
    expect(sourceUses(sources, checks, 'It is 82.5 % [2].')).toEqual([
      { ...sources[0], cited: false, supports: ['R2 within its limit'] },
      { ...sources[1], cited: true, supports: ['R2 within its limit', 'Every figure has a source'] },
    ]);
  });
});
