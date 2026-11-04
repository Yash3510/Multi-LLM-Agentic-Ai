// Keycap legends for shortcuts, as each platform prints them on its keys, with a spoken name
// wherever a screen reader would misread or skip the symbol. Legends are not translated: they
// match the physical keys.

export interface Keycap {
  legend: string;
  /** Read instead of the legend; absent when the legend reads well as it is. */
  spoken?: string;
}

const MAC: Record<string, Keycap> = {
  mod: { legend: '⌘', spoken: 'Command' },
  alt: { legend: '⌥', spoken: 'Option' },
  ctrl: { legend: '⌃', spoken: 'Control' },
  shift: { legend: '⇧', spoken: 'Shift' },
};

const OTHERS: Record<string, Keycap> = {
  mod: { legend: 'Ctrl' },
  alt: { legend: 'Alt' },
  ctrl: { legend: 'Ctrl' },
  shift: { legend: 'Shift' },
};

const SHARED: Record<string, Keycap> = {
  enter: { legend: '↵', spoken: 'Enter' },
  backspace: { legend: '⌫', spoken: 'Backspace' },
  esc: { legend: 'Esc' },
  tab: { legend: 'Tab' },
  space: { legend: 'Space' },
  up: { legend: '↑', spoken: 'Up arrow' },
  down: { legend: '↓', spoken: 'Down arrow' },
  left: { legend: '←', spoken: 'Left arrow' },
  right: { legend: '→', spoken: 'Right arrow' },
};

/**
 * One key by name: mod (⌘ on Apple, Ctrl elsewhere), alt, ctrl, shift, enter, backspace, esc,
 * tab, space and the arrows; any other key is shown as given, single letters in capitals.
 */
export function keycap(key: string, apple: boolean): Keycap {
  const name = key.toLowerCase();
  const known = (apple ? MAC : OTHERS)[name] ?? SHARED[name];
  if (known) return known;
  return { legend: key.length === 1 ? key.toUpperCase() : key };
}

/** True on Apple platforms, whose shortcuts use ⌘ rather than Ctrl. */
export function isApple(): boolean {
  const nav = globalThis.navigator as
    (Navigator & { userAgentData?: { platform?: string } }) | undefined;
  return /mac|iphone|ipad/i.test(nav?.userAgentData?.platform || nav?.platform || '');
}

// Key names as aria-keyshortcuts spells them (the UI Events key values).
const ARIA: Record<string, string> = {
  ctrl: 'Control',
  alt: 'Alt',
  shift: 'Shift',
  enter: 'Enter',
  backspace: 'Backspace',
  esc: 'Escape',
  tab: 'Tab',
  space: 'Space',
  up: 'ArrowUp',
  down: 'ArrowDown',
  left: 'ArrowLeft',
  right: 'ArrowRight',
};

/** The aria-keyshortcuts value for a combination: ['mod', 'k'] is Meta+K on Apple, Control+K elsewhere. */
export function ariaShortcut(keys: string[], apple: boolean): string {
  return keys
    .map((key) => {
      const name = key.toLowerCase();
      if (name === 'mod') return apple ? 'Meta' : 'Control';
      return ARIA[name] ?? (key.length === 1 ? key.toUpperCase() : key);
    })
    .join('+');
}
