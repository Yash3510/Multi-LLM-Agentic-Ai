import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { removeSplash } from './splash';

const web = join(import.meta.dirname, '../../..');
const read = (path: string) => readFileSync(join(web, path));

describe('splash (entry look E0)', () => {
  const shell = read('src/app.html').toString();

  it('shows the brand-kit mark for each theme before the app loads', () => {
    expect(shell).toContain('id="splash"');
    expect(shell).toContain('%sveltekit.assets%/brand/4ce-logomark-ink.svg');
    expect(shell).toContain('%sveltekit.assets%/brand/4ce-logomark-white.svg');
  });

  it('serves the brand-kit files unchanged', () => {
    for (const file of ['4ce-logomark-ink.svg', '4ce-logomark-white.svg']) {
      expect(read(`static/brand/${file}`).equals(read(`src/lib/ui/brand/${file}`))).toBe(true);
    }
  });

  it('is removed at once when the app starts', () => {
    document.body.innerHTML = '<div id="splash"></div><main></main>';
    removeSplash();
    expect(document.getElementById('splash')).toBeNull();
    expect(document.querySelector('main')).not.toBeNull();
  });
});
