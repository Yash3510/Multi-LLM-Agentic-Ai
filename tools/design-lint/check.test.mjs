import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { RULES, lintDir } from './check.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const bad = join(here, 'fixtures/bad');
const good = join(here, 'fixtures/good');
const forbidden = join(bad, 'Forbidden.svelte');
const shell = join(bad, 'app.html');
const cli = (dir) =>
  spawnSync(process.execPath, [join(here, 'check.mjs'), dir], { encoding: 'utf8' });

describe('design lint', () => {
  const hits = lintDir(bad);

  it('reports every rule', () => {
    expect(new Set(hits.map((hit) => hit.rule))).toEqual(new Set(RULES.map((rule) => rule.id)));
  });

  it('flags every forbidden line in the fixture', () => {
    const expected = readFileSync(forbidden, 'utf8')
      .split('\n')
      .flatMap((text, index) =>
        text.trim() && !/^<\/?style>$/.test(text.trim()) ? [index + 1] : [],
      );
    const flagged = new Set(hits.filter((hit) => hit.file === forbidden).map((hit) => hit.line));
    expect([...flagged].sort((a, b) => a - b)).toEqual(expected);
  });

  it('allows raw colours in the token files only', () => {
    expect(hits.filter((hit) => hit.file !== forbidden && hit.file !== shell)).toEqual([]);
  });

  // The splash in app.html paints before any stylesheet loads, so it may name a token's exact
  // value (ADR-0041 amendment); a value no token holds still fails.
  it('lets app.html use a hex colour only when a token file holds that exact value', () => {
    expect(hits.filter((hit) => hit.file === shell).map((hit) => [hit.line, hit.text])).toEqual([
      [2, '#171717'],
    ]);
    expect(lintDir(good)).toEqual([]);
  });

  it('passes code that uses tokens', () => {
    expect(lintDir(good)).toEqual([]);
  });

  it('exits 1 on a hit and 0 when clean', () => {
    expect(cli(bad).status).toBe(1);
    expect(cli(good).status).toBe(0);
  });
});
