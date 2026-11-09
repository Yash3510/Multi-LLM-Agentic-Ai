// What a knowledge row says (workspace F60): its badges and its second line.
import type { KnowledgeBase } from '$lib/data';

type Row = Pick<
  KnowledgeBase,
  'description' | 'files' | 'meta' | 'source' | 'provider' | 'sourceName' | 'auth' | 'writable'
>;

/** Connected bases name their provider and are read-only; so is a local base the person cannot
 * change. */
export function badges(base: Row): string[] {
  if (base.source === 'connected') return [base.provider || 'Connected', 'Read Only'];
  return base.writable ? [] : ['Read Only'];
}

/** The file count, then the source details or the metadata, then the description. */
export function summary(base: Row): string {
  const files =
    base.files === undefined ? [] : [`${base.files} ${base.files === 1 ? 'file' : 'files'}`];
  const details =
    base.source === 'connected'
      ? [base.provider, base.sourceName, base.auth]
      : Object.entries(base.meta ?? {})
          .filter(([, value]) => value)
          .map(([key, value]) => `${key}: ${value}`);
  return [...files, ...details, base.description]
    .filter((part): part is string => !!part)
    .join(' · ');
}

const SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB'];

/** A document's size: steps of 1024, always one decimal ("2.0 KB"), zero as "0 B". */
export function fileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  let size = bytes;
  let unit = 0;
  while (size >= 1024 && unit < SIZE_UNITS.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(1)} ${SIZE_UNITS[unit]}`;
}
