import { describe, expect, it } from 'vitest';
import { ago } from './ago';
import { badges, fileSize, summary } from './knowledge';

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
  const before = (seconds: number) => ago(new Date(now.getTime() - seconds * 1000), now);

  it('words ages as the running app does', () => {
    expect(before(30)).toBe('a few seconds ago');
    expect(before(60)).toBe('a minute ago');
    expect(before(10 * 60)).toBe('10 minutes ago');
    expect(before(60 * 60)).toBe('an hour ago');
    expect(before(3 * 3600)).toBe('3 hours ago');
    expect(before(24 * 3600)).toBe('a day ago');
    expect(before(3 * 86_400)).toBe('3 days ago');
    expect(before(30 * 86_400)).toBe('a month ago');
    expect(before(61 * 86_400)).toBe('2 months ago');
    expect(before(400 * 86_400)).toBe('a year ago');
    expect(before(800 * 86_400)).toBe('2 years ago');
  });
});

describe('file size (workspace F75)', () => {
  it('steps by 1024 with one decimal, as the running app writes it', () => {
    expect(fileSize(0)).toBe('0 B');
    expect(fileSize(512)).toBe('512.0 B');
    expect(fileSize(2048)).toBe('2.0 KB');
    expect(fileSize(1331)).toBe('1.3 KB');
    expect(fileSize(5 * 1024 * 1024)).toBe('5.0 MB');
  });
});
