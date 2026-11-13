import { fireEvent, render, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { createFakeSource } from '$lib/data/fake';
import AdminConnections from './AdminConnections.svelte';

describe('admin connections (admin look §22, local only)', () => {
  it('shows the local model server and leaves out direct connections', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByText, queryByText, getByRole } = render(AdminConnections, { props: { source } });
    expect(await findByText('http://localhost:1234/v1')).toBeTruthy();
    expect(getByRole('switch', { name: 'Ollama API' })).toBeTruthy();
    expect(queryByText('Direct Connections')).toBeNull();
  });

  it('adds a local connection and refuses a public one', async () => {
    const source = createFakeSource({ pace: 0 });
    const { findByRole, getByRole, findByText } = render(AdminConnections, { props: { source } });
    await fireEvent.click(await findByRole('button', { name: 'Add Connection' }));
    const dialog = await findByRole('dialog', { name: 'Add Connection' });
    await fireEvent.input(within(dialog).getByRole('textbox', { name: 'URL' }), {
      target: { value: 'https://api.openai.com/v1' },
    });
    await fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }));
    expect(await findByText(/only on this machine or a private network/)).toBeTruthy();
    await fireEvent.input(within(dialog).getByRole('textbox', { name: 'URL' }), {
      target: { value: 'http://192.168.1.20:8000/v1' },
    });
    await fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }));
    expect(await findByText('http://192.168.1.20:8000/v1')).toBeTruthy();
    await fireEvent.click(getByRole('button', { name: 'Save' }));
    await waitFor(async () =>
      expect(JSON.stringify(await source.getAdminSettings('connections'))).toContain(
        '192.168.1.20',
      ),
    );
  });
});
