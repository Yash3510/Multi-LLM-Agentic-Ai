import { describe, expect, it } from 'vitest';
import { cloneDraft, commandFrom, isCommand, readPromptFile } from './prompts';

describe('prompt commands (workspace F93)', () => {
  it('follows the name as lowercase words joined by hyphens', () => {
    expect(commandFrom('Summarise This Report!')).toBe('summarise-this-report');
    expect(commandFrom('  Unit   101B check ')).toBe('unit-101b-check');
  });

  it('allows letters, digits, hyphens and underscores only', () => {
    expect(isCommand('unit-101b_check')).toBe(true);
    expect(isCommand('unit check')).toBe(false);
    expect(isCommand('')).toBe(false);
  });
});

describe('cloning a prompt (F92)', () => {
  it('suffixes the name and the command, and keeps text and tags', () => {
    expect(
      cloneDraft({ name: 'Brief', command: 'brief', content: 'Be brief.', tags: ['ops'] }),
    ).toEqual({
      name: 'Brief (Clone)',
      command: 'brief-clone',
      content: 'Be brief.',
      tags: ['ops'],
    });
  });
});

describe('prompt files (F88, F92)', () => {
  it('reads only command, name and content from each imported entry', () => {
    expect(
      readPromptFile(
        JSON.stringify([
          { command: '/brief', name: 'Brief', content: 'Be brief.', tags: ['x'], active: false },
        ]),
      ),
    ).toEqual([{ command: 'brief', name: 'Brief', content: 'Be brief.', tags: [] }]);
  });

  it('refuses a file that is not a list', () => {
    expect(() => readPromptFile('{"name":"x"}')).toThrow('The file must hold a list of prompts.');
  });
});
