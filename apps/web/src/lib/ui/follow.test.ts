import { describe, expect, it } from 'vitest';
import { nearBottom } from './follow';

const box = (scrollTop: number) => ({ scrollTop, scrollHeight: 1000, clientHeight: 600 });

describe('nearBottom', () => {
  it('follows while the reader is within 80 px of the end', () => {
    expect(nearBottom(box(400))).toBe(true);
    expect(nearBottom(box(330))).toBe(true);
    expect(nearBottom(box(300))).toBe(false);
  });
});
