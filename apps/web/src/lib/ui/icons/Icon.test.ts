import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { ICONS } from './generated/icons';
import Icon from './Icon.svelte';

const svgOf = (container: HTMLElement) => container.querySelector('svg')!;

describe('Icon', () => {
  it('is hidden from assistive technology without a label', () => {
    const svg = svgOf(render(Icon, { name: 'copy' }).container);
    expect(svg.getAttribute('aria-hidden')).toBe('true');
    expect(svg.hasAttribute('role')).toBe(false);
    expect(svg.getAttribute('width')).toBe('20');
  });

  it('is a named image with a label', () => {
    const { getByRole } = render(Icon, { name: 'copy', label: 'Copy' });
    expect(getByRole('img', { name: 'Copy' }).hasAttribute('aria-hidden')).toBe(false);
  });

  it('draws the Lucide shapes as a 1.75 round stroke in the current colour', () => {
    const svg = svgOf(render(Icon, { name: 'verdict-pass', size: 16 }).container);
    expect(svg.getAttribute('fill')).toBe('none');
    expect(svg.getAttribute('stroke')).toBe('currentColor');
    expect(svg.getAttribute('stroke-width')).toBe('1.75');
    expect(svg.getAttribute('stroke-linecap')).toBe('round');
    expect(svg.children).toHaveLength(ICONS['verdict-pass'].length);
    expect(svg.querySelector('circle')!.getAttribute('r')).toBe('10');
  });
});
