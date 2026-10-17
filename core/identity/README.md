# fource-identity

Users, passwords, sign-in tokens, lockout and roles. This part holds the roles, the sign-in errors, argon2id password hashing and signed tokens; users, sign-in, lockout and sign-out arrive on top of it.

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
| `read_token(token, secret)` | The payload of a valid token; expired, forged, unsigned, other-key and incomplete tokens all raise `NotAuthenticated` |

## Tests

```
uv run pytest core/identity
```
