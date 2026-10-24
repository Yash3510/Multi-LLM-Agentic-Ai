---
title: Identity
type: architecture
status: active
owner: R1
updated: 2026-10-24
covers:
  - core/identity/
tags: [4ce, architecture, identity, security]
---

# Identity

Who a person is and how they prove it: users, passwords, lockout, signed tokens and sign-out. The code is [`core/identity`](../../core/identity/README.md); the HTTP side is the [API](api.md). Route guards per role are planned (WP-ID-02); today every signed-in user can use every endpoint.

## Users and roles

- A **user** belongs to one organisation. Email is unique per organisation, stored trimmed and lower-case, at most 320 characters. The display name is plain text of up to 200 characters.
- Text the database can't hold (a NUL, a lone surrogate) is refused before it reaches the database.
- **Seven roles:** Admin, Author, Reviewer, Viewer, Auditor, Pack Author, Pack Approver. A user holds a list of them. These are *user* roles; agent roles are a different list ([frontend](frontend.md#user-roles-and-agent-roles-are-different-lists)).
- **Roles and the active flag are read from the database on every request,** so a change applies at once, whatever the token says (ADR-0038). An inactive user cannot sign in.

## Passwords

- **argon2id** with the library's current parameters (`argon2-cffi`). A hash is re-made at sign-in when the parameters have moved on.
- **Length: 12 to 1024 characters** when a password is set (`weak_password`, 422). Sign-in accepts 1 to 1024 characters in the request; a longer one is a `validation_failed`.
- No other composition rules.

## Lockout

- **5 failed sign-ins lock the account for 15 minutes.** The failure is counted in the database in one statement, so guesses sent together can't overwrite each other's count. A success resets the count.
- **An unknown email, an inactive user and a wrong password give the same error,** `invalid_credentials`, and the same work: for an unknown email, the password is still verified against a real hash, so timing reveals nothing.
- **A locked account answers `423 account_locked` before the password is checked,** even for the right password. This reveals that the account exists and is locked: a known trade-off, recorded in [ADR-0038](../adr/0038-signed-tokens-for-sign-in.md#consequences).

## Tokens

- **HS256 JWT,** signed with `FOURCE_SECRET_KEY`. Verification accepts HS256 only.
- **Fields, all required:** `sub` (user id), `org` (organisation id), `jti` (token id), `iat`, `exp`. A token with a missing or non-text id is refused.
- **Lifetime:** `FOURCE_TOKEN_TTL_MINUTES`, 480 (8 hours) by default.
- **Revocation:** signing out stores the `jti` until the token's expiry; an expired record is deleted at the next sign-out. A revoked token is `not_authenticated`. Signing out twice is fine.
- **Any failure to read a token** (expired, forged, other key, wrong algorithm, bad fields) is `not_authenticated` (401, "Sign in again.").
- Rotating `FOURCE_SECRET_KEY` signs everyone out.
- **Not done yet:** tokens are not invalidated when a password changes (future work; there is no password-change feature yet).

## Browsers: cookies and CSRF

The server puts the token in an HttpOnly cookie and a second, readable cookie for CSRF; scripts send `Authorization: Bearer` instead. **The rule:** a request authenticated by the cookie, with a method other than GET, HEAD or OPTIONS, must send `X-CSRF-Token` equal to the `fource_csrf` cookie, or it is `csrf_failed`. A bearer request needs no CSRF token, because a cross-site page can't set that header. Names, flags and examples are in the [API](api.md#cookies-and-csrf).

## Creating users

`create_user(session, email=, password=, roles=, display_name=)` validates, hashes and adds the user in the session's organisation. From the command line: `fource-server create-user <email> --role Admin [--name …]`, which asks for the password twice ([API](api.md#running-it)). There is no sign-up endpoint.

## Decisions

[ADR-0038](../adr/0038-signed-tokens-for-sign-in.md): signed tokens instead of server-side sessions, cookies, CSRF and revocation. Where the rows live: [database](database.md).
