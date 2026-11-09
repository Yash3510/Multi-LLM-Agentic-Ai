import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import SkillEditor from './SkillEditor.svelte';
import SkillList from './SkillList.svelte';

const skill = {
  id: 'ratio-check',
  name: 'Ratio Check',
  description: 'Checks ratios.',
  instructions: '# Steps',
  active: false,
  updated: new Date(Date.now() - 3600_000),
  owner: { name: 'asha rao' },
  writable: true,
};

describe('skill list (workspace F101 to F103)', () => {
  it('shows the id, age, Inactive badge and description', () => {
    const { getByText } = render(SkillList, { props: { skills: [skill] } });
    expect(getByText('/ratio-check')).toBeTruthy();
    expect(getByText('an hour ago')).toBeTruthy();
    expect(getByText('Inactive')).toBeTruthy();
    expect(getByText('Checks ratios.')).toBeTruthy();
  });

  it('shows no controls on a skill the person cannot change', () => {
    const { queryByRole } = render(SkillList, {
      props: { skills: [{ ...skill, writable: false }] },
    });
    expect(queryByRole('switch')).toBeNull();
    expect(queryByRole('button', { name: 'Skill Menu' })).toBeNull();
  });
});

describe('skill editor (F105)', () => {
  it('makes the id from the name and fills empty fields from front matter', async () => {
    const source = createFakeSource({ pace: 0 });
    const onsaved = vi.fn();
    const { getByPlaceholderText, getByRole } = render(SkillEditor, { props: { source, onsaved } });
    await fireEvent.input(getByPlaceholderText('Enter skill instructions in markdown...'), {
      target: { value: '---\nname: unit audit\ndescription: Audits a unit\n---\nSteps.' },
    });
    expect((getByPlaceholderText('Skill Name') as HTMLInputElement).value).toBe('Unit Audit');
    expect((getByPlaceholderText('Skill ID') as HTMLInputElement).value).toBe('unit-audit');
    expect((getByPlaceholderText('Skill Description') as HTMLInputElement).value).toBe(
      'Audits a unit',
    );
    await fireEvent.click(getByRole('button', { name: 'Save & Create' }));
    await waitFor(async () => expect(await source.getSkill('unit-audit')).toBeTruthy());
    expect(onsaved).toHaveBeenCalled();
  });

  it('keeps a switched-off skill off when it is saved', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.createSkill({ id: 'a', name: 'A', description: 'D', instructions: 'I' });
    await source.setSkillActive('a', false);
    const existing = (await source.getSkill('a'))!;
    const { getByRole } = render(SkillEditor, { props: { source, skill: existing } });
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () => expect((await source.getSkill('a'))?.active).toBe(false));
  });
});
