---
title: "Signed tokens for sign-in"
type: adr
status: planned
owner: R1
updated: 2026-10-24
covers: []
tags: [4ce, adr]
number: 38
decision_status: proposed
superseded_by: null
---

# ADR-0038: Signed tokens for sign-in

## Context

Master plan §7.3 asks for server-side sessions. On 2026-10-12 the project lead chose signed JWTs instead.

## Decision

1. **A sign-in issues a JWT** signed with HS256 and `FOURCE_SECRET_KEY`, carrying the user, the organisation, a unique token id, and its issue and expiry times. Lifetime: `FOURCE_TOKEN_TTL_MINUTES` (480 by default). Verification accepts HS256 only and requires every field.
2. **Browsers carry it in an HttpOnly, SameSite=Strict cookie;** scripts send it as `Authorization: Bearer`.
3. **CSRF:** a cookie-authenticated state-changing request must send `X-CSRF-Token` matching the readable `fource_csrf` cookie set at sign-in. Bearer requests need no token: a cross-site page can't set that header.
4. **Revocation:** signing out records the token id until its expiry; a revoked token is refused.
5. **Roles and the active flag are read from the database on every request,** so a change takes effect at once, whatever the token says.
6. **Kept from §7.3:** argon2id passwords, lockout after 5 failures for 15 minutes, the seven roles.

## Alternatives considered

| Option | Why not |
| --- | --- |
| Server-side sessions (the plan's original) | The project lead chose tokens |
| Tokens in browser storage | Readable by any script on the page; the HttpOnly cookie isn't |
| Long-lived tokens with no revocation | A stolen token would stay valid until expiry |

## Consequences

- Session fixation doesn't apply (every sign-in issues a new token); the plan's acceptance tests become: CSRF, revocation, lockout, expiry and forged tokens.
- Rotating `FOURCE_SECRET_KEY` signs everyone out.
- A locked account answers `423 account_locked` before the password is checked, so anyone can learn that an account exists and is locked. Accepted for now: a clear message beats hiding it, and the lock lasts 15 minutes.
- Tokens are not invalidated when a password changes. Future work, with the password-change feature.

## Status

Proposed on 2026-10-12, decided by the project lead. To be accepted by R1.
