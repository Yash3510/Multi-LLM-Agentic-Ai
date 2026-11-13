import { describe, expect, it } from 'vitest';
import { feedbackCsv, leaderboardRows, sortRows, share, weekly } from './evaluations';

const models = [
  { id: 'a', name: 'Alpha' },
  { id: 'b', name: 'Beta' },
  { id: 'c', name: 'Gamma' },
];

describe('leaderboard (admin F97 to F103)', () => {
  it('joins models with their stats, adds removed models, ranks rated ones first', () => {
    const rows = leaderboardRows(models, [
      { modelId: 'b', rating: 1016, won: 1, lost: 0, tags: [] },
      { modelId: 'gone', rating: 984, won: 0, lost: 1, tags: [] },
    ]);
    expect(rows.map((row) => [row.id, row.rank])).toEqual([
      ['b', 1],
      ['gone', 2],
      ['a', undefined],
      ['c', undefined],
    ]);
    expect(rows[1].name).toBe('gone');
  });

  it('sorts by name ascending first and by numbers descending first, unrated last', () => {
    const rows = leaderboardRows(models, [
      { modelId: 'c', rating: 1010, won: 2, lost: 1, tags: [] },
    ]);
    expect(sortRows(rows, { column: 'name', ascending: true }).map((row) => row.id)).toEqual([
      'a',
      'b',
      'c',
    ]);
    expect(sortRows(rows, { column: 'won', ascending: false })[0].id).toBe('c');
  });

  it('writes a share with one decimal', () => {
    expect(share(5, 8)).toBe('62.5%');
    expect(share(0, 0)).toBe('-');
  });
});

describe('feedback export (admin F117)', () => {
  it('writes the CSV columns in order and quotes awkward values', () => {
    const csv = feedbackCsv([
      {
        id: 'f1',
        userId: 'u1',
        chatId: 'c1',
        modelId: 'a',
        siblings: ['b', 'c'],
        rating: 8,
        reason: 'clear, "short"',
        comment: 'line\nbreak',
        created: 1,
        updated: 2,
      },
    ]);
    expect(csv.split('\n')[0]).toBe(
      'id,user_id,chat_id,model_id,sibling_model_ids,rating,reason,comment,created_at,updated_at',
    );
    expect(csv).toContain('f1,u1,c1,a,b;c,8,"clear, ""short""","line\nbreak",1,2');
    expect(feedbackCsv([])).toBe('');
  });
});

describe('activity buckets (admin F111)', () => {
  it('sums days into Monday weeks', () => {
    const days = [
      { date: '2026-11-08', won: 1, lost: 0 },
      { date: '2026-11-09', won: 2, lost: 1 },
      { date: '2026-11-11', won: 0, lost: 3 },
    ];
    expect(weekly(days)).toEqual([
      { date: '2026-11-02', won: 1, lost: 0 },
      { date: '2026-11-09', won: 2, lost: 4 },
    ]);
  });
});
