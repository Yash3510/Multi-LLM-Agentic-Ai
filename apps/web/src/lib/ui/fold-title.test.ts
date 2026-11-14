import { describe, expect, it } from 'vitest';
import { foldTitle } from './fold-title';

describe('foldTitle', () => {
  it('splits a role, its step, a verdict and a model', () => {
    expect(foldTitle('Challenger — verification — PASS · qwen/qwen3-1.7b')).toEqual({
      text: 'Challenger · verification',
      verdict: 'PASS',
      model: 'qwen/qwen3-1.7b',
    });
  });

  it('keeps a model without a verdict', () => {
    expect(foldTitle('Analyst — analysis · qwen/qwen3-8b')).toEqual({
      text: 'Analyst · analysis',
      model: 'qwen/qwen3-8b',
    });
  });

  it('leaves a plain title alone', () => {
    expect(foldTitle('Full provenance')).toEqual({ text: 'Full provenance' });
  });

  it('does not take a dotted phrase without a slash for a model', () => {
    expect(foldTitle('Notes · draft')).toEqual({ text: 'Notes · draft' });
  });
});
