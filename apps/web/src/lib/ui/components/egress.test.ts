import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import EgressIndicator from './EgressIndicator.svelte';

describe('EgressIndicator', () => {
  it('renders nothing until a poll has answered', () => {
    const { container } = render(EgressIndicator, {});
    expect(container.querySelector('a')).toBeNull();
  });

  it('names the count and where it leads, and marks the state', () => {
    const clean = render(EgressIndicator, { external: 0 });
    const link = clean.getByRole('link', {
      name: 'Egress: 0 external connections. Open the Sovereignty page.',
    });
    expect(link.dataset.state).toBe('clean');
    clean.unmount();

    const one = render(EgressIndicator, { external: 1 });
    expect(
      one.getByRole('link', { name: 'Egress: 1 external connection. Open the Sovereignty page.' })
        .dataset.state,
    ).toBe('alert');
    one.unmount();

    const stale = render(EgressIndicator, { external: 0, stale: true });
    const staleLink = stale.getByRole('link', {
      name: 'Egress: not observed. Open the Sovereignty page.',
    });
    expect(staleLink.dataset.state).toBe('stale');
    expect(staleLink.textContent).toContain('egress not observed');
  });
});
