import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import UserMenu from './UserMenu.svelte';

const user = { id: 'u1', name: 'Asha Rao', email: 'asha@example.test', role: 'admin' as const };

describe('user menu (layout F125 to F132)', () => {
  it('lists the person, the destinations, Settings and Sign Out', async () => {
    const { findByRole, getByText } = render(UserMenu, {
      props: {
        open: true,
        user,
        active: 2,
        onsettings: vi.fn(),
        onstatus: vi.fn(),
        onsignout: vi.fn(),
      },
    });
    expect(await findByRole('menuitem', { name: /Asha Rao/ })).toBeTruthy();
    expect(getByText('2')).toBeTruthy();
    for (const name of ['Update your status', 'Workspace', 'Settings', 'Sign Out']) {
      expect(getByText(name)).toBeTruthy();
    }
  });

  it('opens Settings', async () => {
    const onsettings = vi.fn();
    const { findByRole } = render(UserMenu, {
      props: { open: true, user, active: 1, onsettings, onstatus: vi.fn(), onsignout: vi.fn() },
    });
    await fireEvent.click(await findByRole('menuitem', { name: 'Settings' }));
    expect(onsettings).toHaveBeenCalled();
  });
});
