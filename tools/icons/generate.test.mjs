import { describe, expect, it } from 'vitest';
import { build, checkRegistry, iconsModule, licenceComment, readPhosphor } from './generate.mjs';

const svg = (inner) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor">${inner}</svg>`;

describe('readPhosphor', () => {
  it('keeps the one path and nothing from the wrapper', () => {
    expect(readPhosphor(svg('<path d="M224,128a8,8,0,0,1-8,8Z"/>'))).toBe('M224,128a8,8,0,0,1-8,8Z');
  });

  it('refuses anything but a single plain path on the 256 grid', () => {
    expect(() => readPhosphor(svg('<g><path d="M0 0"/></g>'))).toThrow(/g/);
    expect(() => readPhosphor(svg('<path d="M0 0" opacity="0.2"/>'))).toThrow(/opacity/);
    expect(() => readPhosphor(svg('<path d="M0 0"/><path d="M1 1"/>'))).toThrow(/one path/);
    expect(() => readPhosphor(svg(''))).toThrow(/one path/);
    expect(() => readPhosphor(svg('<path d="M0 0"/>').replace('0 0 256 256', '0 0 24 24'))).toThrow(
      /256/,
    );
  });
});

describe('checkRegistry', () => {
  it('reports bad names, weights, missing glyphs and malformed entries', () => {
    const has = (glyph) => glyph === 'check';
    expect(
      checkRegistry(
        {
          ok: { phosphor: 'check' },
          bold: { phosphor: 'check', weight: 'bold' },
          filled: { phosphor: 'check', weight: 'fill' },
          Bad: { phosphor: 'check' },
          gone: { phosphor: 'nope' },
          heavy: { phosphor: 'check', weight: 'duotone' },
          odd: {},
        },
        has,
      ),
    ).toEqual([
      'Bad: names are kebab-case',
      'gone: @phosphor-icons/core has no regular glyph "nope"',
      'heavy: weight is regular, bold or fill',
      'odd: needs a "phosphor" glyph name',
    ]);
  });
});

describe('build', () => {
  it('builds the real registry without a problem', () => {
    const { errors, icons } = build();
    expect(errors).toEqual([]);
    expect(Object.keys(icons)).toContain('verdict-pass');
  });

  it('writes the names as a type and the paths as data', () => {
    const module = iconsModule({ check: 'M229.66,77.66Z' });
    expect(module).toContain("export type IconName = 'check';");
    expect(module).toContain('"M229.66,77.66Z"');
  });
});

describe('licenceComment', () => {
  it('wraps the licence in a legal comment the minifier keeps, and cannot be closed early', () => {
    const comment = licenceComment('MIT License\n\nCopyright (c) 2023 Phosphor Icons\nend */ here');
    expect(comment.startsWith('/*!\n * @license Phosphor Icons')).toBe(true);
    expect(comment).toContain(' * Copyright (c) 2023 Phosphor Icons');
    expect(comment.match(/\*\//g)).toHaveLength(1);
    expect(comment.endsWith(' */')).toBe(true);
  });

  it('sits directly on the path table, which the bundle keeps', () => {
    expect(iconsModule({ x: 'M0Z' }, 'MIT License')).toMatch(/ \*\/\nexport const ICONS/);
  });
});
