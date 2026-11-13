import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import ModelRow from './ModelRow.svelte';
import WorkspaceTabs from './WorkspaceTabs.svelte';

describe('WorkspaceTabs', () => {
  it('lists the five tabs in order with their counts and marks the current one', () => {
    const { getAllByRole } = render(WorkspaceTabs, {
      props: {
        current: 'models',
        counts: { models: 0, knowledge: 3, prompts: 0, skills: 0, tools: 1200 },
      },
    });
    const links = getAllByRole('link');
    expect(links.map((link) => link.textContent?.replace(/\s+/g, ' ').trim())).toEqual([
      'Models 0',
      'Knowledge 3',
      'Prompts 0',
      'Skills 0',
      'Tools 1.2K',
    ]);
    expect(links[0].getAttribute('aria-current')).toBe('page');
    expect(links[1].hasAttribute('aria-current')).toBe(false);
  });
});

describe('ModelRow', () => {
  const model = {
    id: 'ratio-checker',
    name: 'Ratio checker',
    base: 'qwen/qwen3-8b',
    updated: new Date(Date.now() - 2 * 86_400_000),
    enabled: true,
    hidden: true,
    writable: false,
  };

  it('falls back to the base model, dims a hidden model and marks read-only', () => {
    const { container, getByText } = render(ModelRow, { props: { model } });
    expect(getByText('qwen/qwen3-8b', { selector: '.description' })).toBeTruthy();
    expect(container.querySelector('[data-hidden]')).toBeTruthy();
    expect(getByText('Read Only')).toBeTruthy();
    expect(getByText('2 days ago')).toBeTruthy();
  });
});
