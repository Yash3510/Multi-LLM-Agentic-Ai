<script lang="ts">
  // The rich-text area (notes look §2): Tiptap with the starter kit and a placeholder, reading
  // and writing Markdown so stored notes stay plain text. A change of `value` from outside (such
  // as Enhance streaming in) replaces the content without echoing back.
  import { Editor } from '@tiptap/core';
  import Placeholder from '@tiptap/extension-placeholder';
  import { Markdown } from '@tiptap/markdown';
  import StarterKit from '@tiptap/starter-kit';
  import { onDestroy, untrack } from 'svelte';

  type Props = {
    value: string;
    onchange: (markdown: string) => void;
    placeholder?: string;
    label?: string;
    readonly?: boolean;
    /** Hands the editor to the caller (tests and toolbars). */
    oneditor?: (editor: Editor) => void;
  };

  let { value, onchange, placeholder = '', label, readonly = false, oneditor }: Props = $props();

  let editor = $state<Editor>();
  let last = untrack(() => value);

  function mount(node: HTMLElement) {
    const created = new Editor({
      element: node,
      extensions: [StarterKit, Placeholder.configure({ placeholder }), Markdown],
      content: untrack(() => value),
      contentType: 'markdown',
      editable: !untrack(() => readonly),
      editorProps: {
        attributes: {
          'aria-label': untrack(() => label) ?? '',
          role: 'textbox',
          'aria-multiline': 'true',
        },
      },
      onUpdate: ({ editor: current }) => {
        last = current.getMarkdown().trimEnd();
        onchange(last);
      },
    });
    editor = created;
    oneditor?.(created);
  }

  $effect(() => {
    const next = value;
    if (editor && next !== last) {
      last = next;
      editor.commands.setContent(next, { contentType: 'markdown', emitUpdate: false });
    }
  });

  $effect(() => {
    editor?.setEditable(!readonly);
  });

  onDestroy(() => editor?.destroy());
</script>

<div class="rich" {@attach mount}></div>

<style>
  .rich {
    font-size: var(--text-ui);
    line-height: 1.6;
  }

  .rich :global(.ProseMirror) {
    min-block-size: 100%;
    outline: none;
  }

  .rich :global(.ProseMirror p.is-editor-empty:first-child::before) {
    float: inline-start;
    block-size: 0;
    color: var(--color-gray-400);
    content: attr(data-placeholder);
    pointer-events: none;
  }

  .rich :global(.ProseMirror :is(h1, h2, h3)) {
    margin-block: 0.8em 0.4em;
    font-weight: var(--font-weight-medium);
  }

  .rich :global(.ProseMirror h1) {
    font-size: 1.4em;
  }

  .rich :global(.ProseMirror h2) {
    font-size: 1.2em;
  }

  .rich :global(.ProseMirror :is(ul, ol)) {
    padding-inline-start: 1.4em;
  }

  .rich :global(.ProseMirror ul) {
    list-style: disc;
  }

  .rich :global(.ProseMirror ol) {
    list-style: decimal;
  }

  .rich :global(.ProseMirror blockquote) {
    padding-inline-start: 12px;
    border-inline-start: 2px solid var(--color-gray-200);
    color: var(--color-gray-600);
  }

  .rich :global(.ProseMirror code) {
    padding: 1px 4px;
    border-radius: 4px;
    background-color: var(--color-gray-100);
    font-family: var(--font-mono);
    font-size: 0.9em;
  }

  .rich :global(.ProseMirror pre) {
    padding: 12px;
    border-radius: 8px;
    background-color: var(--color-gray-50);
    font-family: var(--font-mono);
    font-size: 0.9em;
  }

  :global([data-theme='dark']) .rich :global(.ProseMirror :is(code, pre)) {
    background-color: var(--color-gray-850);
  }
</style>
