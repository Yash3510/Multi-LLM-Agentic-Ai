// The option shape shared by Select, Combobox, RadioGroup and SegmentedControl, and the Combobox's
// filter. Kept out of the components so it can be tested without a DOM.

export interface FieldOption {
  value: string;
  label: string;
  /** A second line under the label, where the control has room for it (RadioGroup). */
  description?: string;
  disabled?: boolean;
}

// Latin accents only. Devanagari vowel signs are combining marks too, but they change the word, so
// they must never be stripped.
const LATIN_ACCENTS = /[\u0300-\u036f]/g;
// Letters, their signs and digits: anything else before a match makes it the start of a word.
const WORD_CHAR = /[\p{L}\p{M}\p{N}]/u;

/** Case- and accent-insensitive form of a label or query, with runs of space collapsed. */
export function fold(text: string): string {
  return text
    .normalize('NFKD')
    .replace(LATIN_ACCENTS, '')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * The options whose label contains the query: first those that start with it, then those with a
 * word that starts with it, then the rest, each group in its original order. An empty query keeps
 * every option. Disabled options stay, so the list still shows why they cannot be picked.
 */
export function filterOptions<T extends FieldOption>(options: readonly T[], query: string): T[] {
  const needle = fold(query);
  if (!needle) return [...options];

  const starts: T[] = [];
  const words: T[] = [];
  const inside: T[] = [];
  for (const option of options) {
    const label = fold(option.label);
    const at = label.indexOf(needle);
    if (at === 0) starts.push(option);
    else if (at > 0) (WORD_CHAR.test(label[at - 1]) ? inside : words).push(option);
  }
  return [...starts, ...words, ...inside];
}
