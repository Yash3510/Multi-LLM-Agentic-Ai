# fource-identity

Users, passwords, sign-in tokens, lockout and roles: the roles, the sign-in errors, argon2id password hashing, signed tokens, the user and revoked-token tables, and sign-in, lockout and sign-out on top of them.

**Owner:** R1 · **Decisions:** [ADR-0038](../../docs/adr/0038-signed-tokens-for-sign-in.md)

## Public API

| Name | What it is |
| --- | --- |
| `Role` | The seven roles: Admin, Author, Reviewer, Viewer, Auditor, Pack Author, Pack Approver |
| `InvalidCredentials`, `AccountLocked`, `NotAuthenticated`, `WeakPassword`, `InvalidEmail`, `EmailTaken` | The errors a sign-in or a password can raise, each with its code and HTTP status |
| `hash_password(password)` | An argon2id hash; refuses a password outside `MIN_PASSWORD_LENGTH` to `MAX_PASSWORD_LENGTH` characters (12 to 1024) before hashing anything |
| `verify_password(stored, password)` | True only when the password matches; a damaged hash is simply false |
| `needs_rehash(stored)` | True when a stored hash uses older parameters than today's |
| `issue_token(user_id=, org_id=, secret=, ttl=)` | A signed HS256 token and its payload (`user_id`, `org_id`, `token_id`, `expires_at`) |
| `read_token(token, secret)` | The payload of a valid token; expired, forged, unsigned, other-key, incomplete and mistyped tokens all raise `NotAuthenticated` |
| `User`, `RevokedToken` | The `users` and `revoked_tokens` tables, both confined to one organisation. A user has `email`, `display_name`, `password_hash`, `roles`, `is_active`, `failed_signins` and `locked_until`; a revoked token has `token_id` and `expires_at` |
| `create_user(session, email=, password=, roles=, display_name=)` | Adds a user. The email is trimmed and lower-cased, so it is unique whatever its case; raises `InvalidEmail`, `EmailTaken` or `WeakPassword`, and `ValueError` for a role that does not exist |
| `sign_in(session, email=, password=, secret=, ttl=)` | Returns `SignedIn` (the user and a token). An unknown or deactivated user and a wrong password raise the same `InvalidCredentials`, and an unknown email spends the same hashing time as a real attempt. `MAX_FAILED_SIGNINS` (5) wrong passwords lock the account for `LOCK_DURATION` (15 minutes), during which even the right password raises `AccountLocked`; the count is committed before the error is raised, so it survives. A success clears the count and upgrades an out-of-date password hash |
| `authenticate(session, payload)` | The active user a token belongs to, read from the database on every call; a revoked token, a missing or deactivated user and a token from another organisation raise `NotAuthenticated` |
| `sign_out(session, payload)` | Revokes the token until it would have expired anyway, and forgets revocations that have expired |

## Tests

```
uv run pytest core/identity
```
