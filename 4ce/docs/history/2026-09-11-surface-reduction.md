---
title: Withdrawing the surfaces that could leave the premises
type: git-history
status: historical
date: 2026-09-11
commits: [339636c, 61de603, 12d2d87, e872139, b9a1a81, 9232d5f, 304bb75, b55ba41, 9339c0a, 777a46b]
authors: [grizzly077, Yash Kumar Singh]
tags:
  - 4ce
  - git-history
  - security
---

# Withdrawing the surfaces that could leave the premises

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `339636c` | 2026-09-11 | grizzly077 | Withdraw the Integrations and About settings panes |
| `61de603` | 2026-09-11 | grizzly077 | Drop the Help block from admin settings |
| `12d2d87` | 2026-09-18 | Yash Kumar Singh | Keep the microphone on-premise and drop the unused surfaces |
| `e872139` | 2026-09-19 | Yash Kumar Singh | Offer only the models the orchestrator routes to |
| `b9a1a81` | 2026-09-19 | Yash Kumar Singh | Remove the two settings that would send data off the premises |
| `9232d5f` | 2026-09-20 | Yash Kumar Singh | Withdraw the Integrations panes for real, not just visually |
| `304bb75` | 2026-09-20 | Yash Kumar Singh | Blank the third-party image endpoints on install |
| `b55ba41` | 2026-09-20 | Yash Kumar Singh | Audit the egress paths the audit was not looking at |
| `9339c0a` | 2026-09-20 | Yash Kumar Singh | Blank the speech endpoints too, not just the image ones |
| `777a46b` | 2026-09-20 | Yash Kumar Singh | Hide the generation parameters that cannot do anything here |

## Summary

Every control that could send data off the machine, or that did nothing in
this build, was withdrawn or neutralised. The sovereignty audit grew from 11
checks to 18 to cover the surfaces it had not been reading.

## Why it changed

The build's claim is that nothing leaves the premises. Each surface below was
one click away from contradicting that claim, or at least looking as if it
did, to anyone auditing the settings screens.

## Files changed

- `src/lib/components/chat/SettingsModal.svelte`, `chat/MessageInput/InputMenu.svelte`,
  `chat/Settings/Audio.svelte`, `chat/Settings/Account/UserProfileImage.svelte`,
  `chat/Settings/Advanced/AdvancedParams.svelte`, `admin/Settings/General.svelte`,
  `layout/Sidebar.svelte`
- `4ce/install.py`, `4ce/tools/sovereignty.py`, `4ce/env.sovereign.example`

## Technical changes

| Surface | Why | What was done |
|---|---|---|
| Integrations settings (external tool servers) | Can route a prompt off-premise | First hidden with CSS (`339636c`). That hid it but left it reachable, so the tabs were dropped from the settings list (`9232d5f`) |
| Admin *Help* block | Every link pointed off the product | Removed; version and licence kept (`61de603`) |
| Microphone | With no engine configured it tried to fetch Whisper from HuggingFace; the browser's Web Speech API streams audio to Google or Microsoft | Whisper weights pre-cached locally, engine kept local (`12d2d87`); the browser option removed (`b9a1a81`) |
| Gravatar | Sends a hash of the account's email to a third party | Removed (`b9a1a81`) |
| Calendar, automations, channels, easter eggs | Unused surface area | Disabled in the environment template (`12d2d87`) |
| Model picker | Listed an embedding model, a 27B that does not fit, and a stock "Arena Model" | Restricted to the routed models on install (`e872139`) |
| Image and speech endpoints | Shipped pointing at `api.openai.com` and `api.mistral.ai` | Blanked on install (`304bb75`, `9339c0a`) |
| "Attach Webpage" | Makes the server fetch any URL; the permission guarding it is bypassed for admins | Withdrawn from the input menu (`b55ba41`) |
| Ollama-only generation parameters | No effect with an OpenAI-compatible server | Hidden (`777a46b`) |

**Audit coverage** (`b55ba41`). The sovereignty check read 11 of 11 while not
looking at the web fetcher. It now also checks web page fetching, image
generation and editing, speech to text, text to speech, external tool servers
and terminal servers: 18 checks.

The upstream licence attribution in the admin panel was deliberately left in
place (`b9a1a81`).

## Impact

Settings held in the application database (the model picker and the blanked
endpoints) are restored by `install.py` after a rebuild. Otherwise they would
revert silently.

## Related documentation

- [SECURITY.md](../../../SECURITY.md)
- [ADR-0007](../decisions/0007-observe-egress-rather-than-assert-it.md)
- [Timeline](README.md)
