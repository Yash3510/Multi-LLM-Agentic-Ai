import { describe, expect, it } from 'vitest';
import { appHref } from './app-href';

describe('appHref', () => {
  it('resolves any in-app path, keeping its search and hash', () => {
    expect(appHref('/workspace/knowledge')).toBe('/workspace/knowledge');
    expect(appHref('/c/abc?x=1#y')).toBe('/c/abc?x=1#y');
  });
});
