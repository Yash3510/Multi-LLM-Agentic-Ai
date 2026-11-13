import { describe, expect, it } from 'vitest';
import { noticesText, packageOf } from './notices.mjs';

describe('packageOf', () => {
  it('names the package a bundled module comes from', () => {
    expect(packageOf('/w/apps/web/node_modules/marked/lib/marked.esm.js')).toBe('marked');
    expect(packageOf('/w/node_modules/@phosphor-icons/core/regular/x.svg')).toBe('@phosphor-icons/core');
    expect(packageOf('/w/node_modules/a/node_modules/b/index.js')).toBe('b');
    expect(packageOf('\0virtual:thing')).toBeUndefined();
    expect(packageOf('/w/apps/web/src/lib/ui/markdown.ts')).toBeUndefined();
  });
});

describe('noticesText', () => {
  it('lists each package once, sorted, with its version, licence and full text', () => {
    const text = noticesText([
      { name: 'marked', version: '18.1.1', license: 'MIT', text: 'MIT License\nmarked' },
      { name: 'dompurify', version: '3.4.17', license: 'Apache-2.0', text: 'Apache text' },
    ]);
    expect(text.indexOf('dompurify 3.4.17')).toBeLessThan(text.indexOf('marked 18.1.1'));
    expect(text).toContain('Licence: Apache-2.0\n\nApache text');
    expect(text).toContain('MIT License\nmarked');
  });

  it('says plainly when a package ships no licence file', () => {
    expect(noticesText([{ name: 'x', version: '1.0.0', license: 'MIT', text: '' }])).toContain(
      'No licence file in the package.',
    );
  });
});
