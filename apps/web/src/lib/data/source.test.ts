import { describe, expect, it } from 'vitest';
import { createFakeSource } from './fake';
import { chooseSource } from './source';

describe('chooseSource', () => {
  it('uses the fake source in dev and in demo builds', () => {
    expect(() => chooseSource({ production: false, demo: false })).not.toThrow();
    expect(() => chooseSource({ production: true, demo: true })).not.toThrow();
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
