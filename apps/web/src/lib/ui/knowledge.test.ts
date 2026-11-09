import { describe, expect, it } from 'vitest';
import { ago } from './ago';
import { badges, summary } from './knowledge';

const base = {
  id: 'a',
  name: 'Plant Notes',
  description: 'Reference readings.',
  updated: new Date(),
  writable: true,
  source: 'local' as const,
};

describe('knowledge row text (workspace F60)', () => {
  it('joins the file count, metadata and description with a middle dot', () => {
    expect(summary({ ...base, files: 2 })).toBe('2 files · Reference readings.');
    expect(summary({ ...base, files: 1, meta: { owner: 'ops', empty: '' } })).toBe(
      '1 file · owner: ops · Reference readings.',
    );
    expect(summary({ ...base, description: '' })).toBe('');
  });

  it('describes a connected source by provider, source name and auth', () => {
    expect(
      summary({
        ...base,
        source: 'connected',
        provider: 'Drive',
        sourceName: 'Shared',
        auth: 'OAuth',
        files: 0,
      }),
    ).toBe('0 files · Drive · Shared · OAuth · Reference readings.');
  });

  it('marks connected and read-only bases', () => {
    expect(badges(base)).toEqual([]);
    expect(badges({ ...base, writable: false })).toEqual(['Read Only']);
    expect(badges({ ...base, source: 'connected', provider: 'Drive' })).toEqual([
      'Drive',
      'Read Only',
    ]);
    expect(badges({ ...base, source: 'connected' })).toEqual(['Connected', 'Read Only']);
  });
});

describe('relative time', () => {
  const now = new Date('2026-11-09T12:00:00Z');
  it('says how long ago, in the largest whole unit', () => {
    expect(ago(new Date('2026-09-09T12:00:00Z'), now)).toBe('2 months ago');
    expect(ago(new Date('2026-11-09T09:00:00Z'), now)).toBe('3 hours ago');
    expect(ago(new Date('2026-11-09T11:59:30Z'), now)).toBe('30 seconds ago');
  });
});
