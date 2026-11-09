import { describe, expect, it } from 'vitest';
import { frontmatter, readSkillFile, skillId } from './skills';

describe('skill ids (workspace F105)', () => {
  it('strips accents, joins words with hyphens and keeps letters, digits, - and _', () => {
    expect(skillId('Résumé Writer v2!')).toBe('resume-writer-v2');
    expect(skillId('unit_101B check')).toBe('unit_101b-check');
  });
});

describe('front matter (F104, F105)', () => {
  it('reads simple key: value lines between the opening dashes', () => {
    expect(
      frontmatter('---\nname: "ratio-check"\ndescription: Checks ratios\n---\n# Body'),
    ).toEqual({
      name: 'ratio-check',
      description: 'Checks ratios',
    });
    expect(frontmatter('# No front matter')).toEqual({});
  });
});

describe('importing skills (F104)', () => {
  it('names a markdown skill from its front matter or its file name', () => {
    expect(readSkillFile('ratio_check.md', '# Steps')).toEqual([
      { id: 'ratio-check', name: 'Ratio Check', description: '', instructions: '# Steps' },
    ]);
    expect(
      readSkillFile('x.md', '---\nname: unit audit\ndescription: Audits\n---\nDo it.'),
    ).toEqual([
      {
        id: 'unit-audit',
        name: 'Unit Audit',
        description: 'Audits',
        instructions: '---\nname: unit audit\ndescription: Audits\n---\nDo it.',
      },
    ]);
  });

  it('takes a JSON list or a single object', () => {
    const one = { id: 'a', name: 'A', description: '', instructions: 'I' };
    expect(readSkillFile('s.json', JSON.stringify(one))).toEqual([one]);
    expect(readSkillFile('s.json', JSON.stringify([one, one]))).toHaveLength(2);
  });
});
