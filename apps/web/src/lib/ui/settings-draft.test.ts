import { describe, expect, it } from 'vitest';
import { draftChanged } from './settings-draft';

const saved = { system: 'Be brief.', params: { temperature: 0.8, seed: 7 } };

describe('general settings draft', () => {
  it('is unchanged when the prompt and parameters match what was saved', () => {
    expect(draftChanged(saved, 'Be brief.', { seed: 7, temperature: 0.8 })).toBe(false);
    expect(draftChanged({ params: {} }, '   ', {})).toBe(false);
  });

  it('is changed by a different prompt', () => {
    expect(draftChanged(saved, 'Be brief', saved.params)).toBe(true);
    expect(draftChanged({ params: {} }, 'Hello', {})).toBe(true);
  });

  it('is changed by an added, removed or different parameter', () => {
    expect(draftChanged(saved, 'Be brief.', { ...saved.params, top_k: 40 })).toBe(true);
    expect(draftChanged(saved, 'Be brief.', { temperature: 0.8 })).toBe(true);
    expect(draftChanged(saved, 'Be brief.', { temperature: 0.7, seed: 7 })).toBe(true);
  });
});
