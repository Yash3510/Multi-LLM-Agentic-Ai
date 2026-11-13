import { describe, expect, it } from 'vitest';
import { GROUPS, chordFrom, conflict, formatChord } from './shortcuts';

describe('keyboard shortcuts (chat-composer F90, F95)', () => {
  it('groups the shortcuts as the running app does', () => {
    expect(GROUPS.map((group) => group.name)).toEqual([
      'Chat',
      'Global',
      'Input',
      'Message',
      'Voice',
    ]);
    expect(GROUPS[0].shortcuts[0]).toMatchObject({ id: 'newChat', label: 'New Chat' });
  });

  it('writes chords with symbols on a Mac and words elsewhere', () => {
    const chord = { mod: true, shift: true, alt: false, key: 'o' };
    expect(formatChord(chord, true)).toBe('⌘⇧O');
    expect(formatChord(chord, false)).toBe('Ctrl + Shift + O');
    expect(formatChord({ mod: true, shift: true, alt: false, key: 'Backspace' }, true)).toBe('⌘⇧⌫');
    expect(formatChord({ mod: false, shift: false, alt: false, key: 'Escape' }, true)).toBe('Esc');
  });

  it('reads a chord from a key press, ignoring a lone modifier', () => {
    expect(chordFrom(new KeyboardEvent('keydown', { key: 'k', metaKey: true }), true)).toEqual({
      mod: true,
      shift: false,
      alt: false,
      key: 'k',
    });
    expect(
      chordFrom(new KeyboardEvent('keydown', { key: 'Shift', shiftKey: true }), true),
    ).toBeUndefined();
  });

  it('names the action a chord is already bound to', () => {
    const bindings = { search: { mod: true, shift: false, alt: false, key: 'k' } };
    expect(conflict(bindings, 'newChat', { mod: true, shift: false, alt: false, key: 'K' })).toBe(
      'Search',
    );
    expect(
      conflict(bindings, 'search', { mod: true, shift: false, alt: false, key: 'k' }),
    ).toBeUndefined();
  });
});
