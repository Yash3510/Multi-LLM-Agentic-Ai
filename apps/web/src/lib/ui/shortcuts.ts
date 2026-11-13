// Keyboard shortcuts (chat-composer features F90, F95): the actions, their default chords, how a
// chord is written (symbols on a Mac, words elsewhere) and read from a key press, and which
// action a chord already belongs to. The asterisk notes are 4CE's own wording.

export interface Chord {
  /** Cmd on a Mac, Ctrl elsewhere. */
  mod: boolean;
  shift: boolean;
  alt: boolean;
  key: string;
}

export interface Shortcut {
  id: string;
  label: string;
  /** The default chord; undefined is Unassigned. Ignored for fixed shortcuts. */
  chord?: Chord;
  /** A fixed shortcut shows this text and cannot be rebound. */
  fixed?: string;
  /** When the shortcut applies, shown on its asterisk. */
  note?: string;
}

const chord = (key: string, mod = true, shift = false, alt = false): Chord => ({
  mod,
  shift,
  alt,
  key,
});

export const GROUPS: { name: string; shortcuts: Shortcut[] }[] = [
  {
    name: 'Chat',
    shortcuts: [
      { id: 'newChat', label: 'New Chat', chord: chord('o', true, true) },
      { id: 'newTemporaryChat', label: 'New Temporary Chat', chord: chord("'", true, true) },
      { id: 'deleteChat', label: 'Delete Chat', chord: chord('Backspace', true, true) },
      { id: 'modelSelector', label: 'Open Model Selector', chord: chord('m', true, true) },
      { id: 'dictation', label: 'Toggle Dictation', chord: chord('l', true, true) },
      { id: 'previousChat', label: 'Navigate to Previous Chat' },
      { id: 'nextChat', label: 'Navigate to Next Chat' },
    ],
  },
  {
    name: 'Global',
    shortcuts: [
      { id: 'search', label: 'Search', chord: chord('k') },
      { id: 'settings', label: 'Open Settings', chord: chord('.') },
      { id: 'shortcuts', label: 'Show Shortcuts', chord: chord('/') },
      { id: 'sidebar', label: 'Toggle Sidebar', chord: chord('s', true, true) },
      { id: 'controls', label: 'Toggle Controls' },
      { id: 'closeModal', label: 'Close Modal', chord: chord('Escape', false) },
    ],
  },
  {
    name: 'Input',
    shortcuts: [
      { id: 'focusInput', label: 'Focus Chat Input', chord: chord('Escape', false, true) },
      {
        id: 'acceptAutocomplete',
        label: 'Accept Autocomplete Generation\nJump to Prompt Variable',
        fixed: 'Tab',
      },
      {
        id: 'pastePlain',
        label: 'Prevent File Creation',
        fixed: 'Ctrl + Shift + V',
        note: 'Pastes long text as text when Paste Large Text as File is on.',
      },
      { id: 'attachKnowledge', label: 'Attach File From Knowledge', fixed: '#' },
      { id: 'customPrompt', label: 'Add Custom Prompt', fixed: '/' },
      { id: 'talkToModel', label: 'Talk to Model', fixed: '@' },
    ],
  },
  {
    name: 'Message',
    shortcuts: [
      {
        id: 'messagePair',
        label: 'Generate Message Pair',
        chord: chord('Enter', true, true),
        note: 'Works while the message box has focus.',
      },
      { id: 'regenerate', label: 'Regenerate Response', chord: chord('r') },
      {
        id: 'allowTool',
        label: 'Allow Tool Call',
        chord: chord('Enter', true, false, true),
        note: 'Works while a tool is waiting for approval.',
      },
      {
        id: 'denyTool',
        label: 'Deny Tool Call',
        chord: chord('Backspace', true, false, true),
        note: 'Works while a tool is waiting for approval.',
      },
      {
        id: 'stop',
        label: 'Stop Generating',
        fixed: 'Esc',
        note: 'Works while an answer is being written.',
      },
      {
        id: 'editLast',
        label: 'Edit Last Message',
        fixed: '↑',
        note: 'Works while the message box is empty and has focus.',
      },
      { id: 'copyLast', label: 'Copy Last Response', chord: chord('c', true, true) },
      { id: 'copyCode', label: 'Copy Last Code Block', chord: chord(';', true, true) },
    ],
  },
  {
    name: 'Voice',
    shortcuts: [
      { id: 'mute', label: 'Toggle Mute', fixed: 'M', note: 'Works during a voice call.' },
    ],
  },
];

const SHORTCUTS = GROUPS.flatMap((group) => group.shortcuts);

const MAC_KEYS: Record<string, string> = {
  Backspace: '⌫',
  Enter: '↩︎',
  Escape: 'Esc',
  ArrowUp: '↑',
  ArrowDown: '↓',
  ArrowLeft: '←',
  ArrowRight: '→',
};
const WORD_KEYS: Record<string, string> = { Escape: 'Esc', ' ': 'Space' };

/** "⌘⇧O" on a Mac, "Ctrl + Shift + O" elsewhere. */
export function formatChord(chord: Chord, mac: boolean): string {
  const key = chord.key.length === 1 ? chord.key.toUpperCase() : chord.key;
  if (mac) {
    return `${chord.mod ? '⌘' : ''}${chord.shift ? '⇧' : ''}${chord.alt ? '⌥' : ''}${MAC_KEYS[key] ?? key}`;
  }
  return [chord.mod && 'Ctrl', chord.shift && 'Shift', chord.alt && 'Alt', WORD_KEYS[key] ?? key]
    .filter(Boolean)
    .join(' + ');
}

const MODIFIERS = ['Shift', 'Control', 'Alt', 'Meta'];

/** The chord a key press makes; a lone modifier makes none yet. */
export function chordFrom(event: KeyboardEvent, mac: boolean): Chord | undefined {
  if (MODIFIERS.includes(event.key)) return undefined;
  return {
    mod: mac ? event.metaKey : event.ctrlKey,
    shift: event.shiftKey,
    alt: event.altKey,
    key: event.key,
  };
}

const same = (a: Chord, b: Chord) =>
  a.mod === b.mod &&
  a.shift === b.shift &&
  a.alt === b.alt &&
  a.key.toLowerCase() === b.key.toLowerCase();

/** The current chord of each configurable shortcut: the person's own, else the default. */
export function bindings(
  own: Record<string, Chord | null> = {},
): Record<string, Chord | undefined> {
  return Object.fromEntries(
    SHORTCUTS.filter((one) => !one.fixed).map((one) => [
      one.id,
      one.id in own ? (own[one.id] ?? undefined) : one.chord,
    ]),
  );
}

/** The label of the other action that already uses the chord, if any. */
export function conflict(
  current: Record<string, Chord | undefined>,
  id: string,
  chord: Chord,
): string | undefined {
  const other = Object.entries(current).find(
    ([key, bound]) => key !== id && bound && same(bound, chord),
  );
  return other && SHORTCUTS.find((one) => one.id === other[0])?.label.split('\n')[0];
}

export const isMac = () => /Mac|iPhone|iPad/.test(globalThis.navigator?.platform ?? '');
