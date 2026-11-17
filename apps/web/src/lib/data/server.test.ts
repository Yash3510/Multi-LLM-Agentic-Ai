import { afterEach, describe, expect, it, vi } from 'vitest';
import { ServerError, serverSession } from './server';

const ADA = {
  id: '6f1c2f7e-5b1a-4c37-9d0e-2a4b8c6d1e3f',
  email: 'ada@example.com',
  display_name: 'Ada Lovelace',
  roles: ['Admin'],
  org: 'default',
};
const SIGNED_IN = { user: ADA, token: 'for-scripts', expires_at: '2026-11-17T20:00:00Z' };

const answer = (status: number, body?: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
const refusal = (status: number, code: string, message: string) =>
  answer(status, { error: { code, message } });

/** Stubs fetch with these outcomes, one per call, and returns it to inspect the calls. */
function serve(...outcomes: (Response | Error)[]) {
  const fetch = vi.fn<typeof globalThis.fetch>();
  for (const outcome of outcomes)
    if (outcome instanceof Error) fetch.mockRejectedValueOnce(outcome);
    else fetch.mockResolvedValueOnce(outcome);
  vi.stubGlobal('fetch', fetch);
  return fetch;
}

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = 'fource_csrf=; max-age=0; path=/';
});

describe('signing in on the server', () => {
  it('posts the email and password as JSON and answers the person', async () => {
    const secret = 'correct-horse-7781';
    const fetch = serve(answer(200, SIGNED_IN));
    const user = await serverSession().signIn('ada@example.com', secret);
    expect(user).toEqual({ id: ADA.id, name: 'Ada Lovelace', email: ADA.email, role: 'admin' });
    const [url, init] = fetch.mock.calls[0];
    expect([url, init?.method]).toEqual(['/api/auth/signin', 'POST']);
    expect(JSON.parse(String(init?.body))).toEqual({ email: ADA.email, password: secret });
    // The password goes into that body only: no answer, storage or address holds it.
    const kept =
      JSON.stringify(user) +
      JSON.stringify({ ...localStorage }) +
      JSON.stringify({ ...sessionStorage }) +
      window.location.href;
    expect(kept).not.toContain(secret);
  });

  it('names a person without a display name by email, and only Admin as an admin', async () => {
    serve(answer(200, { ...SIGNED_IN, user: { ...ADA, display_name: '', roles: ['Reviewer'] } }));
    expect(await serverSession().signIn(ADA.email, 'x')).toMatchObject({
      name: ADA.email,
      role: 'user',
    });
  });

  it.each([
    { status: 401, code: 'invalid_credentials', message: 'The email or password is wrong.' },
    {
      status: 423,
      code: 'account_locked',
      message: 'Too many failed sign-ins. Try again in 15 minutes.',
    },
    {
      status: 429,
      code: 'rate_limited',
      message: 'Too many sign-in attempts from this address. Try again in a minute.',
    },
    {
      status: 503,
      code: 'rate_limit_unavailable',
      message:
        "Signing in is paused: the server can't check its rate limit. Try again in a minute.",
    },
  ])('shows the server message for $code', async ({ status, code, message }) => {
    serve(refusal(status, code, message));
    const error = await serverSession()
      .signIn(ADA.email, 'x')
      .catch((failure: unknown) => failure);
    expect(error).toBeInstanceOf(ServerError);
    expect(error).toMatchObject({ code, status, message });
  });

  it('says the server cannot be reached when no 4CE answer comes back', async () => {
    // No answer at all, then the dev proxy's empty 500 while the server is down.
    serve(new TypeError('Failed to fetch'), new Response('', { status: 500 }));
    for (const attempt of [1, 2])
      await expect(serverSession().signIn(ADA.email, 'x'), `attempt ${attempt}`).rejects.toEqual(
        expect.objectContaining({
          code: 'unreachable',
          message: "Can't reach the 4CE server. Check that it's running, then try again.",
        }),
      );
  });
});

describe('the session on the server', () => {
  it('is the person on 200, and nobody on 401 or when the server is out of reach', async () => {
    const fetch = serve(
      answer(200, ADA),
      refusal(401, 'not_authenticated', 'Sign in again.'),
      new TypeError('Failed to fetch'),
    );
    const session = serverSession();
    expect(await session.currentUser()).toMatchObject({ email: ADA.email, role: 'admin' });
    expect(fetch.mock.calls[0][0]).toBe('/api/auth/session');
    expect(await session.currentUser()).toBeUndefined();
    expect(await session.currentUser()).toBeUndefined();
  });

  it("asks with a load function's own fetch when given one", async () => {
    const global = serve();
    const load = vi.fn<typeof globalThis.fetch>().mockResolvedValue(answer(200, ADA));
    expect(await serverSession().currentUser(load)).toMatchObject({ email: ADA.email });
    expect(load.mock.calls[0][0]).toBe('/api/auth/session');
    expect(global).not.toHaveBeenCalled();
  });
});

describe('signing out on the server', () => {
  it('sends the CSRF cookie as it is at that moment', async () => {
    const fetch = serve(answer(204), answer(204));
    const session = serverSession();
    document.cookie = 'fource_csrf=first-value; path=/';
    await session.signOut();
    // Signing in again replaces the cookie.
    document.cookie = 'fource_csrf=second-value; path=/';
    await session.signOut();
    const sent = fetch.mock.calls.map(([url, init]) => [
      url,
      init?.method,
      new Headers(init?.headers).get('X-CSRF-Token'),
    ]);
    expect(sent).toEqual([
      ['/api/auth/signout', 'POST', 'first-value'],
      ['/api/auth/signout', 'POST', 'second-value'],
    ]);
  });

  it('counts a session that already ended as signed out, and rejects anything else', async () => {
    serve(
      refusal(401, 'not_authenticated', 'Sign in first.'),
      refusal(403, 'csrf_failed', 'Reload the page and try again.'),
      new TypeError('Failed to fetch'),
    );
    const session = serverSession();
    await expect(session.signOut()).resolves.toBeUndefined();
    await expect(session.signOut()).rejects.toMatchObject({
      code: 'csrf_failed',
      message: 'Reload the page and try again.',
    });
    await expect(session.signOut()).rejects.toMatchObject({ code: 'unreachable' });
  });
});

describe('accounts on the server', () => {
  it('has no first-account setup and no sign-up: an administrator adds people', async () => {
    const session = serverSession();
    expect(await session.setupStatus()).toEqual({ firstAccount: false });
    await expect(session.signUp('Ada', ADA.email, 'x')).rejects.toThrow(/administrator/);
    await expect(session.createFirstAccount('Ada', ADA.email, 'x')).rejects.toThrow(
      /administrator/,
    );
  });
});
