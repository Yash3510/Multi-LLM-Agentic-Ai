// Answer markdown to safe HTML (chat-messages look §5): marked parses GitHub-flavoured markdown,
// DOMPurify removes anything that could run (scripts, event handlers, javascript: links). Links
// open in a new tab without handing over the opener.
import DOMPurify from 'dompurify';
import { Marked, type TokenizerAndRendererExtension } from 'marked';
import type { Source } from '$lib/data';

// The sources of the answer being rendered; set per call, read by the citation extension.
let current: Source[] = [];

/** A chip's label (own-4ce look S14): over 30 characters, the first 15, dots, the last 10. */
export const chipLabel = (title: string) =>
  title.length > 30 ? `${title.slice(0, 15)}...${title.slice(-10)}` : title;

const escape = (text: string) =>
  text.replace(
    /[&<>"]/g,
    (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char] ?? char,
  );

// [n] becomes an evidence chip for source n, outside code and only when that source exists.
const citation: TokenizerAndRendererExtension = {
  name: 'citation',
  level: 'inline',
  start: (src) => src.match(/\[\d+\]/)?.index,
  tokenizer(src) {
    const match = /^\[(\d+)\](?!\()/.exec(src);
    const source = match && current.find((item) => item.index === Number(match[1]));
    if (match && source) return { type: 'citation', raw: match[0], source };
    return undefined;
  },
  renderer(token) {
    const source: Source = token.source;
    const name = escape(source.title);
    return `<cite data-source="${source.index}" title="View source: ${name}">${escape(chipLabel(source.title))}</cite>`;
  },
};

const marked = new Marked({ gfm: true, breaks: false, extensions: [citation] });

const purify = DOMPurify();
purify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A' && node.hasAttribute('href')) {
    node.setAttribute('target', '_blank');
    node.setAttribute('rel', 'noopener noreferrer');
  }
});

declare const safe: unique symbol;
/** HTML that came out of DOMPurify. Only this module can make one, so only sanitised HTML can be
 * written to the page through `safeHtml`. */
export type SafeHtml = string & { readonly [safe]: true };

export function renderMarkdown(markdown: string, sources: Source[] = []): SafeHtml {
  current = sources;
  const clean = purify.sanitize(marked.parse(markdown, { async: false }), {
    USE_PROFILES: { html: true },
  });
  // The one place the brand is applied: the string has just come out of DOMPurify.
  return clean as SafeHtml;
}

/** Writes sanitised HTML into an element (a Svelte attachment), in place of {@html}, which the
 * lint rejects for any string: here the type guarantees the string was sanitised. */
export const safeHtml = (html: SafeHtml) => (node: HTMLElement) => {
  node.innerHTML = html;
};
