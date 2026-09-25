---
title: "ADR-0007: Observe egress rather than assert it"
type: decision
status: accepted
updated: 2026-09-25
tags:
  - 4ce
  - decision
  - security
---

# ADR-0007: Observe egress rather than assert it

## Context

The problem statement asks for proof "through logs or a visible network
monitor", not just a statement. 4CE had a configuration audit, which can show
that no external endpoint is configured but cannot see traffic. It also had a
receipt line under every answer reading "0 external calls", which was a
constant (`91152df`).

## Decision

An egress watch in the backend (`utils/fource_egress.py`) samples the
operating system's socket table every 250 ms. It keeps the connections held by
the workbench's own processes (backend, model server, frontend and their
children) and classifies each as loopback, LAN inbound, a configured LAN
endpoint, other LAN outbound, or internet. It needs no admin rights.

The observation is surfaced in several places:

- the Sovereignty page, beside the 18-surface configuration audit, with the
  limits of sampling stated;
- a count in the navbar;
- each answer's receipt, counted over that run, reading "not observed" when
  nothing was watching;
- preflight, which fails if the watch is down;
- a canary that attempts a handshake to a public address and reports
  *Blocked* or *Reachable*. The canary tests the host's egress rule; it is
  logged separately and never counted as external.

## Alternatives considered

- **Configuration audit only.** This was the previous state. It had already
  missed a path once: the audit read 11 of 11 while "Attach Webpage" could make
  the server fetch any URL (`b55ba41`).
- **Packet capture.** Not built. It would close the sampling gaps, but needs
  privileges and belongs on the uplink rather than inside the application.

## Consequences

- On its first run the watch caught the model server contacting a Cloudflare
  address to check for its own updates, while the configuration audit read
  18/18. Firewall rules for Windows and Linux are in
  [HOW_TO_RUN.md](../HOW_TO_RUN.md#making-it-physical).
- The watch is evidence, not a control. Only a host egress rule prevents a
  connection, and the canary is how to show the rule works.
- It cannot see a connection that opens and closes between samples, DNS
  lookups made by the operating system's resolver, or processes outside its
  scope. The page says so.

## Status

Accepted, `91152df` (2026-09-24).

## Related

- [SECURITY.md](../../../SECURITY.md)
- [history/2026-09-24-observed-egress.md](../history/2026-09-24-observed-egress.md)
