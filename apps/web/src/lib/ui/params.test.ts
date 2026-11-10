import { describe, expect, it } from 'vitest';
import { PARAMS, next, setValue, shownParams } from './params';

const param = (key: string) => PARAMS.find((one) => one.key === key)!;

describe('advanced parameters (chat-composer F74)', () => {
  it('lists them in the running app, admin-only ones only for admins', () => {
    expect(
      shownParams(false)
        .map((one) => one.label)
        .slice(0, 4),
    ).toEqual(['Stream Chat Response', 'Function Calling', 'Reasoning Tags', 'Seed']);
    const admin = shownParams(true).map((one) => one.label);
    expect(admin.slice(0, 3)).toEqual([
      'Stream Chat Response',
      'Stream Delta Chunk Size',
      'Context Compaction Threshold',
    ]);
    expect(admin.at(-1)).toBe('use_mlock');
  });

  it('cycles a flag default, on, off and back', () => {
    const stream = param('stream_response');
    expect(next(stream, undefined)).toBe(true);
    expect(next(stream, true)).toBe(false);
    expect(next(stream, false)).toBeUndefined();
  });

  it('turns a number custom at its typical value, and back to default', () => {
    const temperature = param('temperature');
    expect(next(temperature, undefined)).toBe(0.8);
    expect(next(temperature, 0.5)).toBeUndefined();
  });

  it('keeps numbers in range and Top K whole', () => {
    expect(setValue(param('temperature'), '3')).toBe(2);
    expect(setValue(param('top_k'), '12.5')).toBeNull();
    expect(setValue(param('top_k'), '40')).toBe(40);
  });
});
