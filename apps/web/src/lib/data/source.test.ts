import { afterEach, describe, expect, it, vi } from 'vitest';
import { createFakeSource } from './fake';
import { chooseSource } from './source';

describe('chooseSource', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('stays on the fake source throughout in a demo build', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>();
    vi.stubGlobal('fetch', fetch);
    const source = chooseSource({ production: true, demo: true });
    expect(await source.signIn('asha@example.org', 'x')).toMatchObject({ role: 'admin' });
    expect(fetch).not.toHaveBeenCalled();
  });

  it('signs in through the server in a dev build and keeps the fake data for the rest', async () => {
    const user = { id: 'u-1', email: 'ada@example.com', display_name: 'Ada', roles: [], org: 'x' };
    const body = JSON.stringify({ user, token: 't', expires_at: '2026-11-17T20:00:00Z' });
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(new Response(body));
    vi.stubGlobal('fetch', fetch);
    const source = chooseSource({ production: false, demo: false });
    expect(await source.signIn('ada@example.com', 'x')).toMatchObject({ name: 'Ada' });
    expect((await source.listChats()).length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledOnce();
  });

  it('refuses to start a production build on the fake source', () => {
    expect(() => chooseSource({ production: true, demo: false })).toThrow(
      /fake data source is for dev and demo builds only/,
    );
  });
});

describe('fake session', () => {
  it('signs in without keeping the password anywhere', async () => {
    const source = createFakeSource({ pace: 0 });
    const secret = 'correct-horse-7781';
    const user = await source.signIn('asha@example.org', secret);
    expect(user).toMatchObject({ email: 'asha@example.org', role: 'admin' });
    expect(JSON.stringify(user)).not.toContain(secret);
    expect(JSON.stringify(await source.currentUser())).not.toContain(secret);
    const stored = JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage });
    expect(stored).not.toContain(secret);
  });

  it('signs out, signs up and sets up the first account', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.signIn('asha@example.org', 'x');
    await source.signOut();
    expect(await source.currentUser()).toBeUndefined();
    expect((await source.signUp('Ravi Iyer', 'ravi@example.org', 'y')).name).toBe('Ravi Iyer');
    expect(await source.setupStatus()).toEqual({ firstAccount: false });
    const first = await source.createFirstAccount('Meera', 'meera@example.org', 'z');
    expect(first.role).toBe('admin');
  });
});
