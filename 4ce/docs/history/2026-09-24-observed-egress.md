---
title: Observed egress and the Sovereignty page
type: git-history
status: historical
date: 2026-09-24
commits: [91152df]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
  - security
---

# Observed egress and the Sovereignty page

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `91152df` | 2026-09-24 | Yash Kumar Singh | Observe egress rather than assert it |

## Summary

A backend watch now samples what the workbench's own processes connect to,
and the count appears in the navbar, on a Sovereignty page, and in every
answer's receipt. On its first run it caught the model server checking for
updates.

## Why it changed

The problem statement asks for proof "through logs or a visible network
monitor". 4CE had only a configuration audit, plus a receipt line reading "0
external calls" that was a constant.

## Files changed

- `backend/open_webui/utils/fource_egress.py` (486 lines, new), `routers/fource.py` (new), `main.py`
- `src/lib/components/fource/Sovereignty.svelte`, `EgressIndicator.svelte`, `src/routes/(app)/sovereignty/+page.svelte`, `src/lib/apis/fource/index.ts`
- `4ce/tools/sovereignty.py`, `4ce/functions/orchestrator.py`, `4ce/preflight.py`, `4ce/test_tools.py`
- `SECURITY.md`, `README.md`, `4ce/docs/HOW_TO_RUN.md`, `4ce/docs/DEMO_SCRIPT.md`

## Technical changes

- **Egress watch.** Samples the socket table every 250 ms and classifies each
  connection held by the backend, the model server and the frontend dev
  server, and their children: loopback, LAN inbound, configured LAN endpoint,
  other LAN outbound, or internet. It needs no admin rights. On macOS it falls
  back to per-process queries.
- **Canary.** A handshake from the backend to a public address, reported as
  blocked or reachable and logged separately from the external count.
- **Readers.** The Sovereignty page, the navbar count, the per-run receipt
  (which reads "not observed" when nothing was watching), the chat audit, and
  preflight.
- **Routing fix.** The "audit sovereignty" starter prompt matched no audit
  signal and was answered as a document task about pump SOPs. It now routes
  to the audit, and an audit no longer pulls the SOPs in.

## Impact

The watch caught `Bionic.exe` opening a TLS connection to a Cloudflare address
while the configuration audit read 18 of 18. Firewall rules to block it are in
[HOW_TO_RUN.md](../HOW_TO_RUN.md#making-it-physical).

## Related documentation

- [ADR-0007](../decisions/0007-observe-egress-rather-than-assert-it.md)
- [SECURITY.md](../../../SECURITY.md)
- [Timeline](README.md)
