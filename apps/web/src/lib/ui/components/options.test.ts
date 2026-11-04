import { describe, expect, it } from 'vitest';
import { filterOptions, fold, type FieldOption } from './options';

const option = (label: string, disabled = false): FieldOption => ({
  value: label,
  label,
  disabled,
});
const labels = (options: FieldOption[]) => options.map(({ label }) => label);

describe('fold', () => {
  it('ignores case, Latin accents and extra space', () => {
    expect(fold('  Résumé   Ratio ')).toBe('resume ratio');
  });

  it('keeps Devanagari vowel signs, which change the word', () => {
    expect(fold('किरण')).not.toBe(fold('करण'));
    expect(fold('किरण')).toBe('किरण'.normalize('NFKD'));
  });
});

describe('filterOptions', () => {
  const OPTIONS = [
    option('Ratio above limit'),
    option('Rule R2: ratio'),
    option('Duration'),
    option('Operator ratio check'),
    option('Amount in ₹', true),
  ];

  it('keeps every option, in order, for an empty or blank query', () => {
    expect(labels(filterOptions(OPTIONS, ''))).toEqual(labels(OPTIONS));
    expect(labels(filterOptions(OPTIONS, '   '))).toEqual(labels(OPTIONS));
  });

  it('returns a copy, never the caller’s array', () => {
    expect(filterOptions(OPTIONS, '')).not.toBe(OPTIONS);
  });

  it('ranks label starts, then word starts, then matches inside a word', () => {
    expect(labels(filterOptions(OPTIONS, 'ratio'))).toEqual([
      'Ratio above limit',
      'Rule R2: ratio',
      'Operator ratio check',
      'Duration',
    ]);
  });

  it('matches regardless of case and accents', () => {
    expect(labels(filterOptions([option('Résumé'), option('Rest')], 'RESU'))).toEqual(['Résumé']);
  });

  it('keeps disabled options that match', () => {
    expect(filterOptions(OPTIONS, 'amount')).toEqual([OPTIONS[4]]);
  });

  it('matches Devanagari by whole signs, and a sign is not a word boundary', () => {
    const hindi = [option('कारण'), option('किरण'), option('रण नीति')];
    expect(labels(filterOptions(hindi, 'कि'))).toEqual(['किरण']);
    // "रण" starts the third label; inside the first two it follows a vowel sign, so it ranks last.
    expect(labels(filterOptions(hindi, 'रण'))).toEqual(['रण नीति', 'कारण', 'किरण']);
  });

  it('finds nothing when nothing matches', () => {
    expect(filterOptions(OPTIONS, 'CASE-0142')).toEqual([]);
  });
});
