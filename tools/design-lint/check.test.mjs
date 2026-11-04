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
    expect(hits.filter((hit) => hit.file !== forbidden)).toEqual([]);
  });

  it('passes code that uses tokens', () => {
    expect(lintDir(good)).toEqual([]);
  });

  it('exits 1 on a hit and 0 when clean', () => {
    expect(cli(bad).status).toBe(1);
    expect(cli(good).status).toBe(0);
  });
});
