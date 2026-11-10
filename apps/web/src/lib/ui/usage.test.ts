import { describe, expect, it } from 'vitest';
import {
  compact,
  duration,
  heatCells,
  heatColours,
  intensity,
  monthLabels,
  paletteFor,
  showHeat,
  weekStart,
} from './usage';

const day = (date: string, messages = 0, models: Record<string, number> = {}) => ({
  date,
  messages,
  chats: 0,
  tokens: 0,
  models,
});

describe('usage numbers', () => {
  it('writes compact counts and durations like the running app', () => {
    expect(compact(50_200)).toBe('50.2k');
    expect(compact(27_300)).toBe('27.3k');
    expect(compact(8_400)).toBe('8.4k');
    expect(compact(6)).toBe('6');
    expect(duration(0)).toBe('0m');
    expect(duration(125)).toBe('2m');
    expect(duration(3_700)).toBe('1h 1m');
    expect(duration(90_000)).toBe('1d 1h');
  });
});

describe('usage heat map', () => {
  it('grades a day by its messages', () => {
    expect([0, 1, 5, 10, 20].map((messages) => intensity(day('2026-01-01', messages)))).toEqual([
      0, 1, 2, 3, 4,
    ]);
  });

  it('picks a palette by the first letter of the model id, the first for none', () => {
    expect(paletteFor(undefined)).toBe('green');
    expect(paletteFor('4ce-tony')).toBe('green');
    expect(paletteFor('b-model')).toBe('blue');
    expect(paletteFor('qwen/qwen3')).toBe('red');
  });

  it('gives each level its light and dark colour', () => {
    expect(heatColours('green', 0)).toEqual({
      light: 'var(--color-gray-100)',
      dark: 'var(--color-gray-800)',
    });
    expect(heatColours('blue', 2)).toEqual({
      light: 'color-mix(in srgb, var(--color-blue-300) 60%, transparent)',
      dark: 'color-mix(in srgb, var(--color-blue-700) 60%, transparent)',
    });
    expect(heatColours('neutral', 4)).toEqual({
      light: 'var(--color-neutral-800)',
      dark: 'var(--color-neutral-200)',
    });
  });

  it('starts weeks on Monday and shows weekly or running totals per day', () => {
    expect(weekStart('2026-11-12')).toBe('2026-11-09');
    expect(weekStart('2026-11-09')).toBe('2026-11-09');
    const daily = [day('2026-11-09', 1), day('2026-11-10', 2)];
    const weekly = [day('2026-11-09', 3)];
    const shown = showHeat(daily, 'weekly', weekly, []);
    expect(shown.map((one) => [one.date, one.messages])).toEqual([
      ['2026-11-09', 3],
      ['2026-11-10', 3],
    ]);
    expect(showHeat(daily, 'daily', weekly, [])).toBe(daily);
  });

  it('keeps the last whole weeks that fit and pads the last column', () => {
    const days = Array.from({ length: 20 }, (_, index) =>
      day(`2026-01-${String(index + 1).padStart(2, '0')}`),
    );
    const cells = heatCells(days, 2);
    expect(cells).toHaveLength(14);
    expect(cells[0]?.date).toBe('2026-01-07');
    expect(heatCells(days.slice(0, 9), 5)).toHaveLength(14);
    expect(heatCells(days.slice(0, 9), 5).at(-1)).toBeNull();
  });

  it('labels months at least six columns apart', () => {
    const days = Array.from({ length: 70 }, (_, index) => {
      const date = new Date(Date.UTC(2026, 0, 1 + index));
      return day(date.toISOString().slice(0, 10));
    });
    const labels = monthLabels(days, 10, 'en');
    // Feb starts in column 5, too close to Jan in column 1, so it is skipped.
    expect(labels.map((one) => [one.label, one.column, one.span])).toEqual([
      ['Jan', 1, 6],
      ['Mar', 9, 2],
    ]);
  });
});
