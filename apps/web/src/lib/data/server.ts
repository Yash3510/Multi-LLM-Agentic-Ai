// Sign-in, the session and sign-out on the 4CE server (docs/architecture/api.md). Every other
// DataSource call still comes from the fake replay until the server serves it (ADR-0046). The
// browser keeps the HttpOnly session cookie itself, so the token in the sign-in answer is ignored.
import type { DataSource, User } from './types';

/** What the server refused, by its error code, or `unreachable` when no 4CE answer came back. */
export class ServerError extends Error {
  code: string;
  status: number | undefined;

  constructor(code: string, message: string, status?: number) {
    super(message);
    this.name = 'ServerError';
    this.code = code;
    this.status = status;
  }
}

/** A person as the server describes them (UserOut in the OpenAPI document). */
interface ServerUser {
  id: string;
  email: string;
  display_name: string;
  roles: string[];
}

const UNREACHABLE = "Can't reach the 4CE server. Check that it's running, then try again.";
const NO_SIGN_UP = 'This server has no sign-up: an administrator adds people.';

const person = (user: ServerUser): User => ({
  id: user.id,
  name: user.display_name || user.email,
  email: user.email,
  role: user.roles.includes('Admin') ? 'admin' : 'user',
});

/** The server's error envelope, {"error": {"code", "message"}}, when the body is one. */
function refusal(body: unknown): { code: string; message: string } | undefined {
  if (typeof body !== 'object' || body === null || !('error' in body)) return;
  const { error } = body;
  if (typeof error !== 'object' || error === null) return;
  const code = 'code' in error ? error.code : undefined;
  const message = 'message' in error ? error.message : undefined;
  if (typeof code === 'string' && typeof message === 'string') return { code, message };
}

/** Sends one request; anything but a success is thrown as a ServerError. A failure without the
 * envelope (no answer, or a proxy's own error page) didn't come from 4CE, so it is unreachable. */
async function send(path: string, init?: RequestInit, using = fetch): Promise<Response> {
  const response = await using(path, init).catch(() => undefined);
  if (response?.ok) return response;
  const refused = refusal(await response?.json().catch(() => undefined));
  if (refused) throw new ServerError(refused.code, refused.message, response?.status);
  throw new ServerError('unreachable', UNREACHABLE, response?.status);
}

/** Read for each request, because signing in again replaces the cookie. */
const csrfToken = () =>
  document.cookie
    .split('; ')
    .find((pair) => pair.startsWith('fource_csrf='))
    ?.slice('fource_csrf='.length) ?? '';

const refusedWith = (error: unknown, ...codes: string[]) =>
  error instanceof ServerError && codes.includes(error.code);

export function serverSession(): Pick<
  DataSource,
  'currentUser' | 'signIn' | 'signOut' | 'setupStatus' | 'signUp' | 'createFirstAccount'
> {
  return {
    async currentUser(using) {
      try {
        const user: ServerUser = await (await send('/api/auth/session', undefined, using)).json();
        return person(user);
      } catch (error) {
        // Signed out, expired or revoked; or no server to ask, where signing in explains why.
        if (refusedWith(error, 'not_authenticated', 'unreachable')) return undefined;
        throw error;
      }
    },
    async signIn(email, password) {
      const response = await send('/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const { user }: { user: ServerUser } = await response.json();
      return person(user);
    },
    async signOut() {
      try {
        await send('/api/auth/signout', {
          method: 'POST',
          headers: { 'X-CSRF-Token': csrfToken() },
        });
      } catch (error) {
        // The session had already ended (expired or revoked): signed out all the same.
        if (!refusedWith(error, 'not_authenticated')) throw error;
      }
    },
    async setupStatus() {
      return { firstAccount: false };
    },
    async signUp() {
      throw new Error(NO_SIGN_UP);
    },
    async createFirstAccount() {
      throw new Error(NO_SIGN_UP);
    },
  };
}
