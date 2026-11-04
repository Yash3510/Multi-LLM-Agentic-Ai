<script module lang="ts">
  import type { IconName } from '$lib/ui/icons/generated/icons';

  // Only these file glyphs are registered; every other type gets the plain text file.
  const FILE_ICONS: Record<string, IconName> = {
    doc: 'file-doc',
    docx: 'file-doc',
    odt: 'file-doc',
    rtf: 'file-doc',
    xls: 'file-xls',
    xlsx: 'file-xls',
    ods: 'file-xls',
    csv: 'file-xls',
    tsv: 'file-xls',
    ppt: 'file-ppt',
    pptx: 'file-ppt',
    odp: 'file-ppt',
  };

  /** A file name's type as a tag shows it: its extension in capitals and the matching file glyph. */
  export function fileType(name: string): { label: string; icon: IconName } {
    const dot = name.lastIndexOf('.');
    const extension = (dot >= 0 ? name.slice(dot + 1) : name).trim().toLowerCase();
    return { label: extension.toUpperCase(), icon: FILE_ICONS[extension] ?? 'file-text' };
  }
</script>

<script lang="ts">
  // A neutral label: a kind, a pack, a file type, on the faint track (ADR-0037 amendment). It never
  // borrows verdict colours. Not interactive; file tags show their type as text, without a glyph.
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    /** The text; with `file`, defaults to the file's extension. */
    label?: string;
    /** A file name or extension: shows its type as its extension. */
    file?: string;
    /** A Lucide glyph before the label. Decorative, because the label says the same. */
    icon?: IconName;
    /** The label's language when it differs from the page's, e.g. a pack label. */
    lang?: string;
  };

  let { label, file, icon, lang }: Props = $props();

  const type = $derived(file ? fileType(file) : undefined);
  const text = $derived(label ?? type?.label ?? '');
  const glyph = $derived(icon);
</script>

<span
  class="inline-flex h-5.5 max-w-full items-center gap-1 rounded-tag bg-track px-2 text-tag font-medium text-ink-2"
>
  {#if glyph}
    <Icon name={glyph} size={12} />
  {/if}
  <span class="truncate" {lang}>{text}</span>
</span>
