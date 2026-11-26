import { describe, expect, it } from 'vitest';
import { match } from './panel';

describe('the run view panel matcher', () => {
  it('takes the sign-off panel and nothing else', () => {
    expect(match('sign-off')).toBe(true);
    expect(['assessment', 'audit', 'Sign-off', 'sign-off/', ''].map(match)).toEqual([
      false,
      false,
      false,
      false,
      false,
    ]);
  });
});
