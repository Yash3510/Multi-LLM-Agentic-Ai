# Sovereign AI SIH Demo

## Start

1. Start Bionic Studio Local Model API at `http://localhost:1234/v1`.
2. Start local infrastructure with `docker compose up -d --build`.
3. Launch the Tkinter workstation UI with `python -m sovereign_ai`.
4. Create or sign in to the local administrator.
5. Open **Demo guide** and follow the six displayed steps.

## Demonstration path

- Upload a labelled local test inspection document in Knowledge.
- Search the local evidence and inspect its page citation.
- Submit an analysis task and observe Tony, FRIDAY, JARVIS, and ULTRON activity.
- Review the result and choose Approve, Request Changes, or Reject.
- Open Artifacts to inspect generated local files.
- Open the Dashboard/System status views to show model, storage, database, audit, and network policy state.

## Safe prompts

```text
What agents can you work with?
Analyze this inspection report
Create a Python program that calculates total and average employee hours
```

The coding prompt requires human approval and executes only in the Docker sandbox.
