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

export function renderMarkdown(markdown: string): string {
  return purify.sanitize(marked.parse(markdown, { async: false }), {
    USE_PROFILES: { html: true },
  });
}
