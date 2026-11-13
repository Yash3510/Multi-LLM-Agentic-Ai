// What a /ui section file exports from its module script, beside its markup. The page loads every
// file in ./sections, sorted by name, so a new section is a new file and nothing else.
export interface SectionMeta {
  /** The anchor in the page, e.g. "colours". */
  id: string;
  /** Message functions, so the text follows the active locale. */
  title: () => string;
  description?: () => string;
}
