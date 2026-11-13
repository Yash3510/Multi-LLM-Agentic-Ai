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
    expect(svg.getAttribute('width')).toBe('16');
  });

  it('is a named image with a label', () => {
    const { getByRole } = render(Icon, { name: 'copy', label: 'Copy' });
    expect(getByRole('img', { name: 'Copy' }).hasAttribute('aria-hidden')).toBe(false);
  });

  it('fills the Phosphor path on its 256 grid in the current colour', () => {
    const svg = svgOf(render(Icon, { name: 'verdict-pass', size: 18 }).container);
    expect(svg.getAttribute('viewBox')).toBe('0 0 256 256');
    expect(svg.getAttribute('fill')).toBe('currentColor');
    expect(svg.hasAttribute('stroke')).toBe(false);
    expect(svg.getAttribute('width')).toBe('18');
    expect(svg.querySelector('path')!.getAttribute('d')).toBe(ICONS['verdict-pass']);
  });
});
