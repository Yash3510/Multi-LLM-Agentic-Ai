<script lang="ts">
  // The Python code editor (workspace look §9.2): CodeMirror's basic setup (line numbers, folding,
  // active line, bracket matching, autocomplete, search) with Python highlighting, four-space
  // indents, and One Dark in dark mode on a black ground. Ctrl or Cmd+S saves.
  import { indentWithTab } from '@codemirror/commands';
  import { indentUnit } from '@codemirror/language';
  import { python } from '@codemirror/lang-python';
  import { Compartment, EditorState, Prec } from '@codemirror/state';
  import { oneDark } from '@codemirror/theme-one-dark';
  import { EditorView, keymap } from '@codemirror/view';
  import { basicSetup } from 'codemirror';

  type Props = {
    value: string;
    onchange: (value: string) => void;
    onsave?: () => void;
    readonly?: boolean;
  };

  let { value, onchange, onsave, readonly = false }: Props = $props();

  // The running app's editor: 11 px text, no border, white or black ground and gutter.
  const frame = EditorView.theme({
    '&': { height: '100%', fontSize: '11px' },
    '&.cm-focused': { outline: 'none' },
    '.cm-gutters': { border: 'none' },
    '.cm-scroller': { fontFamily: 'var(--font-mono)', lineHeight: '1.4' },
  });
  // The ground lives in the light and dark halves, so the dark one is not outranked.
  const day = EditorView.theme({
    '&': { backgroundColor: 'var(--color-white)' },
    '.cm-gutters': { backgroundColor: 'var(--color-white)' },
  });
  // One Dark on a black ground: the override outranks the theme's own grey ground.
  const night = [
    oneDark,
    Prec.highest(
      EditorView.theme(
        {
          '&': { backgroundColor: 'var(--color-black)' },
          '.cm-gutters': { backgroundColor: 'var(--color-black)' },
        },
        { dark: true },
      ),
    ),
  ];
  const look = new Compartment();
  const isDark = () => document.documentElement.dataset.theme === 'dark';

  const editor = (node: HTMLElement) => {
    const view = new EditorView({
      parent: node,
      state: EditorState.create({
        doc: value,
        extensions: [
          basicSetup,
          python(),
          indentUnit.of('    '),
          keymap.of([
            indentWithTab,
            {
              key: 'Mod-s',
              preventDefault: true,
              run: () => {
                onsave?.();
                return true;
              },
            },
          ]),
          frame,
          look.of(isDark() ? night : day),
          EditorState.readOnly.of(readonly),
          EditorView.updateListener.of((update) => {
            if (update.docChanged) onchange(update.state.doc.toString());
          }),
        ],
      }),
    });
    // Follow the app's theme as it changes.
    const watch = new MutationObserver(() =>
      view.dispatch({ effects: look.reconfigure(isDark() ? night : day) }),
    );
    watch.observe(document.documentElement, { attributeFilter: ['data-theme'] });
    return () => {
      watch.disconnect();
      view.destroy();
    };
  };
</script>

<div class="code" {@attach editor}></div>

<style>
  .code {
    block-size: 100%;
    overflow: hidden;
    border-radius: 8px;
  }
</style>
