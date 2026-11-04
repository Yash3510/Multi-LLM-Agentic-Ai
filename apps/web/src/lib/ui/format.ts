// The one format module (design-system.md, "Numbers, units, times and hashes"): every
// number, unit, time and hash goes through here, so a receipt, a ledger row and a
// printout show the same string.

/** Shown for a value that is missing or not a finite number. */
export const MISSING = '—';
export const DEFAULT_LOCALE = 'en-IN';

// A narrow no-break space joins a number to its unit so the two never wrap apart.
const NNBSP = ' ';
// Between the parts of a duration ("1 min 05 s"): wider than NNBSP so the parts read as
// groups, still unbreakable so a duration never wraps.
const NBSP = ' ';
const MINUS = '−';
const ELLIPSIS = '…';

type Value = number | null | undefined;
type When = Date | number | string | null | undefined;

export interface NumberOptions {
  /** Fixed decimals, as in a table column. Omitted: up to 3, or 3 significant digits. */
  decimals?: number;
  locale?: string;
}

export interface MoneyOptions extends NumberOptions {
  /** The amount's own currency; amounts are never converted. */
  currency?: string;
}

export interface TimeOptions {
  locale?: string;
  /** Omitted: the viewer's time zone. */
  timeZone?: string;
}

/** The Intl locale for an app locale ("en", "hi"); India is the default region. */
export function toIntlLocale(appLocale: string): string {
  return appLocale.includes('-') ? appLocale : `${appLocale}-IN`;
}

// Table cells format thousands of values; building an Intl formatter is the costly part.
const formatters = new Map<string, Intl.NumberFormat | Intl.DateTimeFormat>();

function numberFormat(locale: string, options: Intl.NumberFormatOptions): Intl.NumberFormat {
  const key = `n|${locale}|${JSON.stringify(options)}`;
  let format = formatters.get(key) as Intl.NumberFormat | undefined;
  if (!format) {
    // 'negative' keeps a value that rounds to zero from printing as "-0".
    format = new Intl.NumberFormat(locale, { ...options, signDisplay: 'negative' });
    formatters.set(key, format);
  }
  return format;
}

function dateFormat(locale: string, options: Intl.DateTimeFormatOptions): Intl.DateTimeFormat {
  const key = `d|${locale}|${JSON.stringify(options)}`;
  let format = formatters.get(key) as Intl.DateTimeFormat | undefined;
  if (!format) {
    format = new Intl.DateTimeFormat(locale, options);
    formatters.set(key, format);
  }
  return format;
}

const isNumber = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value);

/** Intl output with a true minus sign, and the percent sign spaced like any unit. */
function intlNumber(value: number, locale: string, options: Intl.NumberFormatOptions): string {
  return numberFormat(locale, options)
    .formatToParts(value)
    .map((part) => {
      if (part.type === 'minusSign') return MINUS;
      if (part.type === 'percentSign') return `${NNBSP}%`;
      // Some locales put their own space before %; ours replaces it.
      if (options.style === 'percent' && part.type === 'literal' && !part.value.trim()) return '';
      return part.value;
    })
    .join('');
}

/** Rounds exactly as Intl prints, so the unit chosen matches the digits shown. */
const round = (value: number, decimals: number): number =>
  Number(numberFormat('en', { maximumFractionDigits: decimals, useGrouping: false }).format(value));

const fixed = (decimals: number): Intl.NumberFormatOptions => ({
  minimumFractionDigits: decimals,
  maximumFractionDigits: decimals,
});

// Without fixed decimals, a small value keeps its significant digits instead of
// rounding to a misleading 0 (0.000012 stays 0.000012, not 0).
const digits = (decimals: number | undefined, maxFraction: number): Intl.NumberFormatOptions =>
  decimals === undefined
    ? {
        maximumFractionDigits: maxFraction,
        maximumSignificantDigits: 3,
        roundingPriority: 'morePrecision',
      }
    : fixed(decimals);

const withUnit = (number: string, unit: string): string =>
  unit ? `${number}${NNBSP}${unit}` : number;

/** A number in the viewer's locale, en-IN by default: `1,23,456.5`, `−12`. */
export function formatNumber(
  value: Value,
  { decimals, locale = DEFAULT_LOCALE }: NumberOptions = {},
): string {
  return isNumber(value) ? intlNumber(value, locale, digits(decimals, 3)) : MISSING;
}

/** A value and its unit, the unit exactly as the pack gives it: `3.7 s`, `4.5 mm/s`. */
export function formatQuantity(value: Value, unit: string, options?: NumberOptions): string {
  return isNumber(value) ? withUnit(formatNumber(value, options), unit) : MISSING;
}

/** A value with its tolerance: `4.5 ± 0.2 mm/s`. Without a tolerance, just the value. */
export function formatTolerance(
  value: Value,
  tolerance: Value,
  unit: string,
  options?: NumberOptions,
): string {
  if (!isNumber(value)) return MISSING;
  if (!isNumber(tolerance)) return formatQuantity(value, unit, options);
  const plusMinus = `${NNBSP}±${NNBSP}${formatNumber(Math.abs(tolerance), options)}`;
  return withUnit(`${formatNumber(value, options)}${plusMinus}`, unit);
}

/** A limit: a maximum prints as `≤ 4.5 mm/s`, a minimum as `≥ 20 count/min`. */
export function formatLimit(
  bound: 'max' | 'min',
  value: Value,
  unit: string,
  options?: NumberOptions,
): string {
  if (!isNumber(value)) return MISSING;
  return `${bound === 'max' ? '≤' : '≥'}${NNBSP}${formatQuantity(value, unit, options)}`;
}

/** A ratio as a percentage: 0.125 prints `12.5 %`. Pack values already in % use formatQuantity. */
export function formatPercent(
  ratio: Value,
  { decimals, locale = DEFAULT_LOCALE }: NumberOptions = {},
): string {
  // Intl's percent style scales by 100 in decimal, so 0.145 is 14.5 % and not 14.499… %.
  return isNumber(ratio)
    ? intlNumber(ratio, locale, { style: 'percent', ...digits(decimals, 1) })
    : MISSING;
}

/** Money in its own currency, ₹ by default: `₹12,34,567.50`, `−₹12.50`. */
export function formatMoney(
  amount: Value,
  { decimals, currency = 'INR', locale = DEFAULT_LOCALE }: MoneyOptions = {},
): string {
  if (!isNumber(amount)) return MISSING;
  return intlNumber(amount, locale, {
    style: 'currency',
    currency,
    ...(decimals === undefined ? {} : fixed(decimals)),
  });
}

/**
 * A duration in seconds: one decimal under 10 s, whole seconds under 60 s, then
 * `1 min 05 s` and `1 h 05 min`. The value is rounded before its unit is chosen, so
 * 9.96 s prints `10 s` and 59.6 s prints `1 min 00 s`.
 */
export function formatDuration(
  seconds: Value,
  { locale = DEFAULT_LOCALE }: Pick<NumberOptions, 'locale'> = {},
): string {
  if (!isNumber(seconds)) return MISSING;
  const abs = Math.abs(seconds);
  const tenths = round(abs, 1);
  const sign = seconds < 0 && tenths > 0 ? MINUS : '';
  const two = (n: number) => intlNumber(n, locale, { minimumIntegerDigits: 2 });
  const whole = round(abs, 0);

  if (tenths < 10) return sign + withUnit(intlNumber(tenths, locale, fixed(1)), 's');
  if (whole < 60) return sign + withUnit(intlNumber(whole, locale, fixed(0)), 's');
  if (whole < 3600) {
    const minutes = withUnit(intlNumber(Math.floor(whole / 60), locale, fixed(0)), 'min');
    return `${sign}${minutes}${NBSP}${withUnit(two(whole % 60), 's')}`;
  }
  const totalMinutes = round(abs / 60, 0);
  const hours = withUnit(intlNumber(Math.floor(totalMinutes / 60), locale, fixed(0)), 'h');
  return `${sign}${hours}${NBSP}${withUnit(two(totalMinutes % 60), 'min')}`;
}

// Decimal (SI) steps, as file sizes are shown by browsers and operating systems.
const BYTE_UNITS = ['B', 'kB', 'MB', 'GB', 'TB', 'PB'];

/** A size in bytes: `512 B`, `1.5 kB`, `12.3 MB`. */
export function formatBytes(
  bytes: Value,
  { locale = DEFAULT_LOCALE }: Pick<NumberOptions, 'locale'> = {},
): string {
  if (!isNumber(bytes)) return MISSING;
  let size = Math.abs(bytes);
  let step = 0;
  // Step up while the printed value would reach 1,000, so 999,960 B is 1 MB, not 1,000 kB.
  while (step < BYTE_UNITS.length - 1 && round(size, step === 0 ? 0 : 1) >= 1000) {
    size /= 1000;
    step += 1;
  }
  const options = { maximumFractionDigits: step === 0 ? 0 : 1 };
  return withUnit(intlNumber(Math.sign(bytes) * size, locale, options), BYTE_UNITS[step]);
}

/** A hash where space is tight: the first 8 characters and an ellipsis. */
export function formatHashShort(hash: string | null | undefined): string {
  const value = hash?.trim();
  if (!value) return MISSING;
  return value.length > 8 ? `${value.slice(0, 8)}${ELLIPSIS}` : value;
}

/**
 * The full hash for detail views and print, in groups of four. Plain spaces let a long
 * hash wrap between groups; copy actions copy the raw hash, not this string.
 */
export function formatHashFull(hash: string | null | undefined): string {
  const value = hash?.trim();
  if (!value) return MISSING;
  return (value.match(/.{1,4}/g) ?? []).join(' ');
}

function toDate(when: When): Date | undefined {
  if (when === null || when === undefined || when === '') return undefined;
  const date = when instanceof Date ? when : new Date(when);
  return Number.isNaN(date.getTime()) ? undefined : date;
}

const CLOCK: Intl.DateTimeFormatOptions = {
  hour: '2-digit',
  minute: '2-digit',
  // en-IN defaults to a 12-hour clock; records use 24-hour time.
  hourCycle: 'h23',
  timeZoneName: 'short',
};

/** A time in the viewer's zone, with the zone named: `14:05 IST`. */
export function formatTime(
  when: When,
  { locale = DEFAULT_LOCALE, timeZone }: TimeOptions = {},
): string {
  const date = toDate(when);
  return date ? dateFormat(locale, { ...CLOCK, timeZone }).format(date) : MISSING;
}

/** A date and time with the zone named: `8 Oct 2026, 14:05 IST`. */
export function formatDateTime(
  when: When,
  { locale = DEFAULT_LOCALE, timeZone }: TimeOptions = {},
): string {
  const date = toDate(when);
  const options = { day: 'numeric', month: 'short', year: 'numeric', ...CLOCK, timeZone } as const;
  return date ? dateFormat(locale, options).format(date) : MISSING;
}

/** ISO 8601 in UTC for exports; empty when there is no time, so exports stay parseable. */
export function formatIso(when: When): string {
  return toDate(when)?.toISOString() ?? '';
}
