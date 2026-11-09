import { describe, expect, it } from 'vitest';
import { STARTER, manifest, readToolFile, toolId } from './tools';

describe('tool ids (workspace F114)', () => {
  it('joins lowercase words with underscores, accents stripped', () => {
    expect(toolId('Unit Convért -- v2!')).toBe('unit_convert_v2');
  });
});

describe('the code header (F114)', () => {
  it('reads key: value lines in the opening triple-quoted block', () => {
    expect(manifest('"""\ntitle: Unit Convert\nversion: 0.2.0\n"""\nclass Tools: pass')).toEqual({
      title: 'Unit Convert',
      version: '0.2.0',
    });
    expect(manifest('class Tools: pass')).toEqual({});
  });
});

describe('the starter (owner: own 4CE starter, offline)', () => {
  it('is a Tools class that makes no network calls', () => {
    expect(STARTER).toContain('class Tools:');
    expect(STARTER).not.toMatch(/requests|urllib|http/);
  });
});

describe('importing tools (F112)', () => {
  it('takes a JSON list and refuses anything else', () => {
    const one = { id: 'a', name: 'A', description: 'D', content: 'x' };
    expect(readToolFile(JSON.stringify([one]))).toEqual([one]);
    expect(() => readToolFile(JSON.stringify(one))).toThrow('The file must hold a list of tools.');
  });
});
