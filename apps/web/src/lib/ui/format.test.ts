import { describe, expect, it } from 'vitest';
import {
  MISSING,
  formatBytes,
  formatDateTime,
  formatDuration,
  formatAgo,
  formatHashFull,
  formatHashShort,
  formatIso,
  formatLimit,
  formatMoney,
  formatNumber,
  formatPercent,
  formatQuantity,
  formatTime,
  formatTolerance,
  timeGroup,
  toIntlLocale,
} from './format';

// Spelled out so a test never passes on a look-alike character.
const NNBSP = ' ';
const NBSP = ' ';
const MINUS = '−';

const notNumbers = [NaN, Infinity, -Infinity, null, undefined];

describe('formatNumber', () => {
  it('groups in lakh and crore by default (en-IN)', () => {
    expect(formatNumber(1234)).toBe('1,234');
    expect(formatNumber(123456)).toBe('1,23,456');
    expect(formatNumber(1234567)).toBe('12,34,567');
    expect(formatNumber(12345678)).toBe('1,23,45,678');
    expect(formatNumber(123456789.5)).toBe('12,34,56,789.5');
  });

  it('prints zero, and never a negative zero', () => {
    expect(formatNumber(0)).toBe('0');
    expect(formatNumber(-0)).toBe('0');
    expect(formatNumber(-0.04, { decimals: 1 })).toBe('0.0');
  });

  it('uses a true minus sign, never a hyphen', () => {
    expect(formatNumber(-1234.5)).toBe(`${MINUS}1,234.5`);
    expect(formatNumber(-12345678)).toBe(`${MINUS}1,23,45,678`);
    expect(formatNumber(-1234.5)).not.toContain('-');
  });

  it('keeps fixed decimals for a table column', () => {
    expect(formatNumber(3.7, { decimals: 2 })).toBe('3.70');
    expect(formatNumber(1234.5, { decimals: 0 })).toBe('1,235');
    expect(formatNumber(2, { decimals: 3 })).toBe('2.000');
  });

  it('shows up to 3 decimals by default, without float noise', () => {
    expect(formatNumber(1234.56789)).toBe('1,234.568');
    expect(formatNumber(0.1 + 0.2)).toBe('0.3');
    expect(formatNumber(2.5)).toBe('2.5');
  });

  it('keeps very small values instead of rounding them to 0', () => {
    expect(formatNumber(0.000012)).toBe('0.000012');
    expect(formatNumber(1.5e-10)).toBe('0.00000000015');
    expect(formatNumber(-0.0001234)).toBe(`${MINUS}0.000123`);
  });

  it('prints very large values in full with Indian grouping', () => {
    expect(formatNumber(1e21)).toBe('1,00,00,00,00,00,00,00,00,00,000');
    expect(formatNumber(Number.MAX_SAFE_INTEGER)).toBe('9,00,71,99,25,47,40,991');
  });

  it('shows the missing mark for anything that is not a finite number', () => {
    for (const value of notNumbers) expect(formatNumber(value)).toBe(MISSING);
  });

  it('follows the locale it is given', () => {
    expect(formatNumber(1234567, { locale: 'hi-IN' })).toBe('12,34,567');
    expect(formatNumber(1234567, { locale: 'en-US' })).toBe('1,234,567');
  });
});

describe('toIntlLocale', () => {
  it('adds the India region to a bare app locale', () => {
    expect(toIntlLocale('en')).toBe('en-IN');
    expect(toIntlLocale('hi')).toBe('hi-IN');
    expect(toIntlLocale('en-GB')).toBe('en-GB');
  });
});

describe('formatQuantity', () => {
  it('joins number and unit with a narrow no-break space', () => {
    expect(formatQuantity(3.7, 's')).toBe(`3.7${NNBSP}s`);
    expect(formatQuantity(4.5, 'mm/s')).toBe(`4.5${NNBSP}mm/s`);
    expect(formatQuantity(20, 'count/min')).toBe(`20${NNBSP}count/min`);
    expect(formatQuantity(123456, 's')).toBe(`1,23,456${NNBSP}s`);
  });

  it('shows the unit exactly as given', () => {
    expect(formatQuantity(12.5, '%')).toBe(`12.5${NNBSP}%`);
    expect(formatQuantity(9.81, 'm/s²')).toBe(`9.81${NNBSP}m/s²`);
  });

  it('handles negatives, fixed decimals, no unit and missing values', () => {
    expect(formatQuantity(-2.5, 's')).toBe(`${MINUS}2.5${NNBSP}s`);
    expect(formatQuantity(3.7, 's', { decimals: 2 })).toBe(`3.70${NNBSP}s`);
    expect(formatQuantity(12, '')).toBe('12');
    for (const value of notNumbers) expect(formatQuantity(value, 's')).toBe(MISSING);
  });
});

describe('formatTolerance', () => {
  it('prints value ± tolerance and the unit once', () => {
    expect(formatTolerance(4.5, 0.2, 'mm/s')).toBe(`4.5${NNBSP}±${NNBSP}0.2${NNBSP}mm/s`);
    expect(formatTolerance(4.5, -0.2, 's', { decimals: 2 })).toBe(
      `4.50${NNBSP}±${NNBSP}0.20${NNBSP}s`,
    );
  });

  it('falls back to the value alone without a tolerance', () => {
    expect(formatTolerance(4.5, undefined, 's')).toBe(`4.5${NNBSP}s`);
    expect(formatTolerance(NaN, 0.2, 's')).toBe(MISSING);
  });
});

describe('formatLimit', () => {
  it('uses ≤ for a maximum and ≥ for a minimum', () => {
    expect(formatLimit('max', 4.5, 'mm/s')).toBe(`≤${NNBSP}4.5${NNBSP}mm/s`);
    expect(formatLimit('min', 20, 'count/min')).toBe(`≥${NNBSP}20${NNBSP}count/min`);
    expect(formatLimit('min', -5, 's')).toBe(`≥${NNBSP}${MINUS}5${NNBSP}s`);
  });

  it('shows the missing mark for a missing limit', () => {
    expect(formatLimit('max', undefined, 's')).toBe(MISSING);
  });
});

describe('formatPercent', () => {
  it('turns a ratio into a percentage spaced like a unit', () => {
    expect(formatPercent(0.125)).toBe(`12.5${NNBSP}%`);
    expect(formatPercent(0)).toBe(`0${NNBSP}%`);
    expect(formatPercent(1)).toBe(`100${NNBSP}%`);
    expect(formatPercent(1 / 3)).toBe(`33.3${NNBSP}%`);
  });

  it('scales in decimal, so 0.145 is 14.5 %', () => {
    expect(formatPercent(0.145)).toBe(`14.5${NNBSP}%`);
    expect(formatPercent(0.07)).toBe(`7${NNBSP}%`);
  });

  it('handles fixed decimals, negatives, tiny and large ratios', () => {
    expect(formatPercent(0.5, { decimals: 2 })).toBe(`50.00${NNBSP}%`);
    expect(formatPercent(-0.05)).toBe(`${MINUS}5${NNBSP}%`);
    expect(formatPercent(0.000012)).toBe(`0.0012${NNBSP}%`);
    expect(formatPercent(12345.6)).toBe(`12,34,560${NNBSP}%`);
    for (const value of notNumbers) expect(formatPercent(value)).toBe(MISSING);
  });
});

describe('formatMoney', () => {
  it('prints rupees with Indian grouping', () => {
    expect(formatMoney(1234567.5)).toBe('₹12,34,567.50');
    expect(formatMoney(0)).toBe('₹0.00');
    expect(formatMoney(1e12)).toBe('₹10,00,00,00,00,000.00');
  });

  it('puts a true minus sign before the symbol and never shows −₹0.00', () => {
    expect(formatMoney(-12.5)).toBe(`${MINUS}₹12.50`);
    expect(formatMoney(-0.004)).toBe('₹0.00');
  });

  it('keeps fixed decimals and the amount’s own currency', () => {
    expect(formatMoney(1234567.5, { decimals: 0 })).toBe('₹12,34,568');
    expect(formatMoney(1234567.5, { currency: 'USD' })).toBe('$12,34,567.50');
    for (const value of notNumbers) expect(formatMoney(value)).toBe(MISSING);
  });
});

describe('formatDuration', () => {
  it('shows one decimal under 10 s', () => {
    expect(formatDuration(0)).toBe(`0.0${NNBSP}s`);
    expect(formatDuration(3.7)).toBe(`3.7${NNBSP}s`);
    expect(formatDuration(9.94)).toBe(`9.9${NNBSP}s`);
    expect(formatDuration(0.0000001)).toBe(`0.0${NNBSP}s`);
  });

  it('rounds before choosing the format: 9.95 s and 10 s both print 10 s', () => {
    expect(formatDuration(9.95)).toBe(`10${NNBSP}s`);
    expect(formatDuration(9.96)).toBe(`10${NNBSP}s`);
    expect(formatDuration(10)).toBe(`10${NNBSP}s`);
  });

  it('shows whole seconds under 60 s, and 59.6 s rounds up to a minute', () => {
    expect(formatDuration(59.4)).toBe(`59${NNBSP}s`);
    expect(formatDuration(59.5)).toBe(`1${NNBSP}min${NBSP}00${NNBSP}s`);
    expect(formatDuration(59.6)).toBe(`1${NNBSP}min${NBSP}00${NNBSP}s`);
  });

  it('shows minutes with padded seconds under an hour', () => {
    expect(formatDuration(65)).toBe(`1${NNBSP}min${NBSP}05${NNBSP}s`);
    expect(formatDuration(3599.4)).toBe(`59${NNBSP}min${NBSP}59${NNBSP}s`);
  });

  it('shows hours with padded minutes from an hour up', () => {
    expect(formatDuration(3599.6)).toBe(`1${NNBSP}h${NBSP}00${NNBSP}min`);
    expect(formatDuration(3900)).toBe(`1${NNBSP}h${NBSP}05${NNBSP}min`);
    expect(formatDuration(3929)).toBe(`1${NNBSP}h${NBSP}05${NNBSP}min`);
    expect(formatDuration(3930)).toBe(`1${NNBSP}h${NBSP}06${NNBSP}min`);
    expect(formatDuration(90000)).toBe(`25${NNBSP}h${NBSP}00${NNBSP}min`);
    expect(formatDuration(3.6e6)).toBe(`1,000${NNBSP}h${NBSP}00${NNBSP}min`);
  });

  it('uses a true minus sign, but never on a value that rounds to zero', () => {
    expect(formatDuration(-3.7)).toBe(`${MINUS}3.7${NNBSP}s`);
    expect(formatDuration(-65)).toBe(`${MINUS}1${NNBSP}min${NBSP}05${NNBSP}s`);
    expect(formatDuration(-0.04)).toBe(`0.0${NNBSP}s`);
  });

  it('shows the missing mark for anything that is not a finite number', () => {
    for (const value of notNumbers) expect(formatDuration(value)).toBe(MISSING);
  });
});

describe('formatBytes', () => {
  it('uses decimal units and stays in bytes under 1 kB', () => {
    expect(formatBytes(0)).toBe(`0${NNBSP}B`);
    expect(formatBytes(512)).toBe(`512${NNBSP}B`);
    expect(formatBytes(999)).toBe(`999${NNBSP}B`);
    expect(formatBytes(1000)).toBe(`1${NNBSP}kB`);
    expect(formatBytes(1536)).toBe(`1.5${NNBSP}kB`);
    expect(formatBytes(12_345_678)).toBe(`12.3${NNBSP}MB`);
    expect(formatBytes(1e15)).toBe(`1${NNBSP}PB`);
  });

  it('steps up a unit when rounding would print 1,000', () => {
    expect(formatBytes(999.6)).toBe(`1${NNBSP}kB`);
    expect(formatBytes(999_960)).toBe(`1${NNBSP}MB`);
  });

  it('caps at PB, keeps the sign and handles missing values', () => {
    expect(formatBytes(1e21)).toBe(`10,00,000${NNBSP}PB`);
    expect(formatBytes(-1536)).toBe(`${MINUS}1.5${NNBSP}kB`);
    for (const value of notNumbers) expect(formatBytes(value)).toBe(MISSING);
  });
});

describe('hashes', () => {
  const hash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';

  it('shortens to 8 characters and an ellipsis', () => {
    expect(formatHashShort(hash)).toBe('e3b0c442…');
    expect(formatHashShort('e3b0c442')).toBe('e3b0c442');
    expect(formatHashShort(`  ${hash}\n`)).toBe('e3b0c442…');
  });

  it('prints the full hash in groups of four', () => {
    expect(formatHashFull(hash)).toBe(
      'e3b0 c442 98fc 1c14 9afb f4c8 996f b924 27ae 41e4 649b 934c a495 991b 7852 b855',
    );
    expect(formatHashFull(hash).replaceAll(' ', '')).toBe(hash);
    expect(formatHashFull('abcdef')).toBe('abcd ef');
  });

  it('shows the missing mark for an empty hash', () => {
    for (const value of ['', '   ', null, undefined]) {
      expect(formatHashShort(value)).toBe(MISSING);
      expect(formatHashFull(value)).toBe(MISSING);
    }
  });
});

describe('times', () => {
  const instant = new Date('2026-10-08T08:35:00Z');
  const india = { timeZone: 'Asia/Kolkata' };

  it('prints 24-hour time with the zone named', () => {
    expect(formatTime(instant, india)).toBe('14:05 IST');
    expect(formatTime('2026-10-08T18:35:00Z', india)).toBe('00:05 IST');
    expect(formatTime(instant, { timeZone: 'UTC' })).toBe('08:35 UTC');
    expect(formatTime(instant.getTime(), india)).toBe('14:05 IST');
  });

  it('uses the viewer’s time zone by default', () => {
    const { timeZone } = Intl.DateTimeFormat().resolvedOptions();
    expect(formatTime(instant)).toBe(formatTime(instant, { timeZone }));
  });

  it('prints the date with the time', () => {
    expect(formatDateTime(instant, india)).toBe('8 Oct 2026, 14:05 IST');
  });

  it('prints ISO 8601 in UTC for exports', () => {
    expect(formatIso(instant)).toBe('2026-10-08T08:35:00.000Z');
    expect(formatIso('2026-10-08T14:05:00+05:30')).toBe('2026-10-08T08:35:00.000Z');
  });

  it('handles missing and invalid times', () => {
    for (const value of ['', 'not a time', NaN, null, undefined, new Date(NaN)]) {
      expect(formatTime(value)).toBe(MISSING);
      expect(formatDateTime(value)).toBe(MISSING);
      expect(formatIso(value)).toBe('');
    }
  });
});

// Local-time constructors, so the calendar-day tests hold in any time zone.
const NOW = new Date(2026, 10, 4, 10, 30);

describe('timeGroup', () => {
  it('bands by calendar day, not by 24-hour spans', () => {
    expect(timeGroup(new Date(2026, 10, 4, 0, 5), NOW)).toEqual({ band: 'today' });
    expect(timeGroup(new Date(2026, 10, 3, 23, 59), NOW)).toEqual({ band: 'yesterday' });
    expect(timeGroup(new Date(2026, 10, 2, 11), NOW)).toEqual({ band: 'week' });
  });

  it('keeps the 7 and 30 day cut-offs inclusive', () => {
    expect(timeGroup(new Date(2026, 9, 28), NOW)).toEqual({ band: 'week' });
    expect(timeGroup(new Date(2026, 9, 27), NOW)).toEqual({ band: 'month' });
    expect(timeGroup(new Date(2026, 9, 5), NOW)).toEqual({ band: 'month' });
  });

  it('names the month in this year, then the year', () => {
    expect(timeGroup(new Date(2026, 9, 4), NOW)).toEqual({ band: 'month-name', month: 9 });
    expect(timeGroup(new Date(2026, 0, 1), NOW)).toEqual({ band: 'month-name', month: 0 });
    expect(timeGroup(new Date(2025, 11, 31), NOW)).toEqual({ band: 'year', year: 2025 });
  });

  it('puts a time ahead of now (clock skew) in today', () => {
    expect(timeGroup(new Date(2026, 10, 6), NOW)).toEqual({ band: 'today' });
  });

  it('has no band for a missing or broken time', () => {
    expect(timeGroup(undefined, NOW)).toBeUndefined();
    expect(timeGroup('not a date', NOW)).toBeUndefined();
  });
});

describe('formatAgo', () => {
  const ago = (ms: number) => formatAgo(NOW.getTime() - ms, { now: NOW });
  const MIN = 60_000;

  it('never shows less than one minute', () => {
    expect(ago(0)).toBe('1m');
    expect(ago(59_000)).toBe('1m');
    expect(ago(-5 * MIN)).toBe('1m');
  });

  it('takes the largest whole unit', () => {
    expect(ago(59 * MIN)).toBe('59m');
    expect(ago(60 * MIN)).toBe('1h');
    expect(ago(23 * 60 * MIN)).toBe('23h');
    expect(ago(6 * 1440 * MIN)).toBe('6d');
    expect(ago(7 * 1440 * MIN)).toBe('1w');
    expect(ago(364 * 1440 * MIN)).toBe('52w');
    expect(ago(730 * 1440 * MIN)).toBe('2y');
  });

  it('localises the unit', () => {
    expect(formatAgo(NOW.getTime() - 3 * 60 * MIN, { now: NOW, locale: 'hi-IN' })).toBe('3 घं');
  });

  it('shows the missing mark for no time', () => {
    expect(formatAgo(null, { now: NOW })).toBe(MISSING);
  });
});
