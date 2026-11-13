// Evaluations rules (admin F97 to F117): the leaderboard rows and their sorting, win shares,
// the feedback CSV export and weekly buckets for the activity chart.
import type { LeaderboardEntry } from '$lib/data';

export interface BoardRow {
  id: string;
  name: string;
  rating?: number;
  won?: number;
  lost?: number;
  /** The true rank by rating, independent of the shown order; unrated models have none. */
  rank?: number;
  tags: LeaderboardEntry['tags'];
}

export type BoardColumn = 'rating' | 'name' | 'won' | 'lost';

/** Every model with its stats, plus stats for models no longer listed; rated first by rating. */
export function leaderboardRows(
  models: { id: string; name: string }[],
  entries: LeaderboardEntry[],
): BoardRow[] {
  const stats = new Map(entries.map((entry) => [entry.modelId, entry]));
  const listed = new Set(models.map((model) => model.id));
  const rows: BoardRow[] = [
    ...models.map((model) => {
      const entry = stats.get(model.id);
      return { id: model.id, name: model.name, ...entry, tags: entry?.tags ?? [] };
    }),
    ...entries
      .filter((entry) => !listed.has(entry.modelId))
      .map((entry) => ({ ...entry, id: entry.modelId, name: entry.modelId })),
  ].map(({ id, name, rating, won, lost, tags }) => ({ id, name, rating, won, lost, tags }));
  const ranked = sortRows(rows, { column: 'rating', ascending: false });
  let rank = 0;
  return ranked.map((row) => ({ ...row, rank: row.rating === undefined ? undefined : ++rank }));
}

/** Names sort as text; numbers sort with unrated rows always last. */
export function sortRows(rows: BoardRow[], sort: { column: BoardColumn; ascending: boolean }) {
  const sign = sort.ascending ? 1 : -1;
  return [...rows].sort((a, b) => {
    if (sort.column === 'name') return sign * a.name.localeCompare(b.name);
    const [x, y] = [a[sort.column], b[sort.column]];
    if (x === undefined || y === undefined) return x === y ? 0 : x === undefined ? 1 : -1;
    return sign * (x - y);
  });
}

/** 5 of 8 → "62.5%"; a dash when there are no results. */
export const share = (part: number, total: number) =>
  total ? `${((part / total) * 100).toFixed(1)}%` : '-';

export interface FeedbackRecord {
  id: string;
  userId: string;
  chatId?: string;
  modelId: string;
  siblings: string[];
  rating?: number;
  reason?: string;
  comment?: string;
  created: number;
  updated: number;
}

const cell = (value: unknown) => {
  const text = value === undefined || value === null ? '' : String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
};

/** The running app's CSV columns, in order; no records make an empty file. */
export function feedbackCsv(records: FeedbackRecord[]): string {
  if (!records.length) return '';
  const head =
    'id,user_id,chat_id,model_id,sibling_model_ids,rating,reason,comment,created_at,updated_at';
  const rows = records.map((one) =>
    [
      one.id,
      one.userId,
      one.chatId,
      one.modelId,
      one.siblings.join(';'),
      one.rating,
      one.reason,
      one.comment,
      one.created,
      one.updated,
    ]
      .map(cell)
      .join(','),
  );
  return [head, ...rows].join('\n');
}

export interface ActivityDay {
  date: string;
  won: number;
  lost: number;
}

/** Days summed into weeks that start on Monday. */
export function weekly(days: ActivityDay[]): ActivityDay[] {
  const weeks = new Map<string, ActivityDay>();
  for (const day of days) {
    const date = new Date(`${day.date}T00:00:00Z`);
    date.setUTCDate(date.getUTCDate() - ((date.getUTCDay() + 6) % 7));
    const key = date.toISOString().slice(0, 10);
    const week = weeks.get(key) ?? { date: key, won: 0, lost: 0 };
    weeks.set(key, { ...week, won: week.won + day.won, lost: week.lost + day.lost });
  }
  return [...weeks.values()];
}
