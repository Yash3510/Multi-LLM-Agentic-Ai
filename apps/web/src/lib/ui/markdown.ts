// Answer markdown to safe HTML (chat-messages look §5): marked parses GitHub-flavoured markdown,
// DOMPurify removes anything that could run (scripts, event handlers, javascript: links). Links
// open in a new tab without handing over the opener.
import DOMPurify from 'dompurify';
import { Marked } from 'marked';

const marked = new Marked({ gfm: true, breaks: false });

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

export function renderMarkdown(markdown: string): SafeHtml {
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
