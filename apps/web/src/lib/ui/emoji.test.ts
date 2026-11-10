import { describe, expect, it } from 'vitest';
import { EMOJI, findEmoji } from './emoji';

describe('emoji search', () => {
  it('finds emoji by name and returns all for an empty search', () => {
    expect(findEmoji('heart').map(([emoji]) => emoji)).toEqual(['❤️']);
    expect(findEmoji('')).toHaveLength(EMOJI.length);
    expect(findEmoji('zzz')).toEqual([]);
  });
});
