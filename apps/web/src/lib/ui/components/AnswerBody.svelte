<script lang="ts">
  // An answer's prose (chat-messages look §5): sanitised markdown with evidence chips for [n],
  // compact lists, quiet tables and code on the code ground. The chat's answers and the run view's
  // draft both show it.
  import { arrive } from '$lib/ui/arrive';
  import { onChip, safeHtml, type SafeHtml } from '$lib/ui/markdown';

  type Props = {
    /** The answer rendered by renderMarkdown, chips included. */
    html: SafeHtml;
    /** Opens source n when its chip is pressed. */
    oncite: (index: number) => void;
    /** Text is still arriving: a caret at its end. */
    typing?: boolean;
  };

  let { html, oncite, typing = false }: Props = $props();
</script>

<div
  class="body"
  data-typing={typing ? '' : undefined}
  {@attach safeHtml(html)}
  {@attach onChip(oncite)}
  {@attach arrive()}
></div>

<style>
  .body {
    color: var(--color-prose);
    font-size: var(--text-body);
    /* The answer prose's relaxed line (24.4 px at 15 px), measured on the running app. */
    line-height: 1.625;
    overflow-wrap: anywhere;
  }

  /* Answer prose (chat-messages look §5): 4 px paragraph margins, compact lists, quiet tables
     and code on the code ground. */
  .body :global(:is(p, ul, ol, table, pre, blockquote)) {
    margin-block: var(--spacing-1);
  }

  .body :global(:is(ul, ol)) {
    padding-inline-start: 1.5em;
  }

  .body :global(ul) {
    list-style: disc;
  }

  .body :global(ol) {
    list-style: decimal;
  }

  .body :global(li) {
    margin-block: 2px;
  }

  .body :global(a) {
    text-decoration: underline;
    text-underline-offset: 2px;
  }

  .body :global(strong) {
    font-weight: var(--font-weight-medium);
  }

  /* A table is one outlined box, like a settings group. */
  .body :global(table) {
    margin-block: 10px 6px;
    overflow: hidden;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-control);
    border-collapse: separate;
    border-spacing: 0;
    font-size: var(--text-small);
  }

  .body :global(:is(th, td)) {
    padding: 6px 14px;
    border-block-end: 1px solid var(--color-line-1);
  }

  .body :global(tr:last-child > td) {
    border-block-end: 0;
  }

  /* Columns marked right-aligned in the markdown (numbers) keep their align attribute. */
  .body :global(:is(th, td):not([align])) {
    text-align: start;
  }

  /* A quiet header row on a soft ground; figures line up down a column. */
  .body :global(th) {
    background-color: var(--glass-soft);
    color: var(--color-ink-3);
    font-size: var(--text-caption);
    font-weight: var(--font-weight-medium);
  }

  .body :global(td) {
    color: var(--color-ink-1);
    font-variant-numeric: tabular-nums;
  }

  .body :global(pre) {
    padding: var(--spacing-3);
    overflow-x: auto;
    border-radius: var(--radius-inset);
    background-color: var(--color-code-ground);
    color: var(--color-code-ink);
    font-size: var(--text-small);
  }

  /* Evidence chips for [n] (own-4ce look S14). */
  .body :global(.chip) {
    display: inline-flex;
    align-items: center;
    max-inline-size: 16rem;
    margin-inline: 3px 1px;
    padding: 0 5px;
    overflow: hidden;
    border: 1px solid var(--color-line-1);
    border-radius: 5px;
    color: var(--color-ink-2);
    font-size: 11px;
    font-style: normal;
    font-weight: var(--font-weight-medium);
    line-height: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: baseline;
    translate: 0 -1px;
    cursor: pointer;
  }

  .body :global(.chip:hover) {
    background-color: var(--glass-soft);
    color: var(--color-ink-1);
  }

  .body :global(:not(pre) > code) {
    padding: 1px 4px;
    border-radius: var(--radius-tight);
    background-color: var(--color-gray-50);
    font-size: 0.9em;
  }

  /* A block written while the answer streams fades in (arrive.ts); saved answers do not. */
  .body > :global([data-arrive]) {
    animation: arrive var(--duration-calm) var(--ease-out) both;
  }

  @keyframes arrive {
    from {
      opacity: 0;
    }
  }

  /* The typing caret at the end of the text while it streams (chat-messages look §3.4). */
  .body[data-typing] > :global(:last-child)::after {
    content: '';
    display: inline-block;
    inline-size: 2px;
    block-size: 14px;
    margin-inline-start: 2px;
    background-color: var(--color-gray-400);
    vertical-align: baseline;
    animation: pulse 1s ease-in-out infinite;
  }

  :global([data-theme='dark']) .body[data-typing] > :global(:last-child)::after {
    background-color: var(--color-gray-500);
  }

  @keyframes pulse {
    50% {
      opacity: 0.3;
    }
  }
</style>
