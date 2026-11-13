import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import NodeGlyph from './NodeGlyph.svelte';

describe('NodeGlyph', () => {
  it('draws a node that mounts finished complete, with no motion', () => {
    const { container } = render(NodeGlyph, { props: { state: 'done' } });
    expect(container.querySelector('svg')?.hasAttribute('data-fresh')).toBe(false);
  });

  it('plays the close when a node finishes in front of the reader', async () => {
    const view = render(NodeGlyph, { props: { state: 'working' } });
    await view.rerender({ state: 'released' });
    expect(view.container.querySelector('svg')?.hasAttribute('data-fresh')).toBe(true);
  });
});
