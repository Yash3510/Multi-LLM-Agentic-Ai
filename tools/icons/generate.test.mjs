import { describe, expect, it } from 'vitest';
import { build, checkRegistry, iconsModule, readLucide } from './generate.mjs';

const svg = (inner) =>
  `<!-- @license lucide-static - ISC -->\n<svg class="lucide" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">\n${inner}\n</svg>`;

describe('readLucide', () => {
  it('keeps each shape and its geometry, nothing from the wrapper', () => {
    expect(readLucide(svg('<circle cx="12" cy="12" r="10" />\n<path d="m9 12 2 2 4-4" />'))).toEqual([
      ['circle', { cx: '12', cy: '12', r: '10' }],
      ['path', { d: 'm9 12 2 2 4-4' }],
    ]);
  });

  it('refuses anything that is not a plain shape', () => {
    expect(() => readLucide(svg('<g><path d="M0 0" /></g>'))).toThrow(/g/);
    expect(() => readLucide(svg('<path d="M0 0" filter="url(#f)" />'))).toThrow(/filter/);
    expect(() => readLucide(svg(''))).toThrow(/no shapes/);
  });
});

describe('checkRegistry', () => {
  it('reports bad names, missing glyphs and malformed entries', () => {
    const has = (glyph) => glyph === 'check';
    expect(
      checkRegistry({ ok: { lucide: 'check' }, Bad: { lucide: 'check' }, gone: { lucide: 'nope' }, odd: {} }, has),
    ).toEqual([
      'Bad: names are kebab-case',
      'gone: lucide-static has no glyph "nope"',
      'odd: needs a "lucide" glyph name',
    ]);
  });
});

describe('build', () => {
  it('builds the real registry without a problem', () => {
    const { errors, icons } = build();
    expect(errors).toEqual([]);
    expect(Object.keys(icons)).toContain('verdict-pass');
  });

  it('writes the names as a type and the shapes as data', () => {
    const module = iconsModule({ check: [['path', { d: 'M20 6 9 17l-5-5' }]] });
    expect(module).toContain("export type IconName = 'check';");
    expect(module).toContain('"M20 6 9 17l-5-5"');
  });
});
