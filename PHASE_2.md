# Phase 2 Runtime

Phase 2 adds the local Stark multi-agent execution loop:

```text
Request -> Tony plan -> FRIDAY analysis -> JARVIS execution -> ULTRON verification
                                      ^                         |
                                      +------ retry ------------+
```

`TaskEngine` persists task and step state in SQLite. Each step records its agent, action, model, input, output, verification, status, timestamps, and errors. ULTRON challenges results and receives one verification retry before a task is marked failed.

The Tkinter chat workspace displays activity events emitted by the real task engine. The local API exposes task state at `GET /api/tasks` and runs orchestrated chat through `POST /api/conversations/{id}/chat`.

All agents use the configured local Bionic Studio model provider. JARVIS is intentionally limited to structured in-process execution; unrestricted host command execution is not enabled.
