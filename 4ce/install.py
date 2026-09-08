"""
Install or refresh the 4CE plugin set in a running 4CE instance.

    python 4ce/install.py --email admin@4ce.local --password <password>

Creates the first admin account if none exists, then uploads the orchestrator
pipe function and the sandbox, deliverables and sovereignty tools, enabling
each one. Safe to re-run: existing plugins are updated in place.

Standard library only, so it runs with any Python 3.11+ interpreter.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FUNCTIONS = [
    ("ace_orchestrator", "4CE Orchestrator", ROOT / "functions" / "orchestrator.py",
     "TONY routes, FRIDAY grounds, JARVIS executes, ULTRON verifies, a human approves."),
]
TOOLS = [
    ("ace_sandbox", "4CE Sovereign Sandbox", ROOT / "tools" / "sandbox.py",
     "Runs Python in a disposable, network-disabled container."),
    ("ace_deliverables", "4CE Deliverables", ROOT / "tools" / "deliverables.py",
     "Produces formatted .docx deliverables from agent output."),
    ("ace_sovereignty", "4CE Sovereignty Check", ROOT / "tools" / "sovereignty.py",
     "Audits live configuration for anything that could send data off-premise."),
]


def call(base, path, token=None, payload=None, method=None):
    url = f"{base.rstrip('/')}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, (json.loads(body) if body.strip() else None)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except ValueError:
            return exc.code, {"detail": body[:400]}
    except urllib.error.URLError as exc:
        return 0, {"detail": f"cannot reach {url}: {exc.reason}"}


def authenticate(base, email, password, name):
    status, body = call(base, "/api/v1/auths/signin", payload={"email": email, "password": password})
    if status == 200 and body and body.get("token"):
        return body["token"], "signed in"
    status, body = call(
        base, "/api/v1/auths/signup",
        payload={"name": name, "email": email, "password": password},
    )
    if status == 200 and body and body.get("token"):
        return body["token"], "created the admin account"
    detail = (body or {}).get("detail", body)
    raise SystemExit(f"Authentication failed ({status}): {detail}")


def deploy(base, token, kind, entries):
    plural = "functions" if kind == "function" else "tools"
    results = []
    for plugin_id, name, path, description in entries:
        if not path.exists():
            results.append((plugin_id, "MISSING", str(path)))
            continue
        payload = {
            "id": plugin_id,
            "name": name,
            "content": path.read_text(encoding="utf-8"),
            "meta": {"description": description, "manifest": {}},
        }
        status, body = call(base, f"/api/v1/{plural}/create", token=token, payload=payload)
        action = "created"
        create_error = (body or {}).get("detail") if status != 200 else None
        if status != 200:
            status, body = call(
                base, f"/api/v1/{plural}/id/{plugin_id}/update", token=token, payload=payload
            )
            action = "updated"
        if status != 200:
            reason = create_error or (body or {}).get("detail", status)
            results.append((plugin_id, "FAILED", str(reason)[:160]))
            continue
        if kind == "function":
            # `toggle` flips state, so re-running would disable an already-enabled
            # function. Only flip when it is actually inactive.
            state_status, state = call(base, f"/api/v1/functions/id/{plugin_id}", token=token)
            if state_status == 200 and not (state or {}).get("is_active"):
                call(base, f"/api/v1/functions/id/{plugin_id}/toggle", token=token, payload={})
        results.append((plugin_id, action.upper(), name))
    return results


def main():
    parser = argparse.ArgumentParser(description="Install the 4CE plugin set.")
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--email", default="admin@4ce.local")
    parser.add_argument("--password", default="4ce-demo-password")
    parser.add_argument("--name", default="4CE Administrator")
    args = parser.parse_args()

    status, _ = call(args.base, "/health")
    if status != 200:
        raise SystemExit(f"4CE is not responding at {args.base} (status {status}). Start the backend first.")

    token, how = authenticate(args.base, args.email, args.password, args.name)
    print(f"Auth: {how}.")

    rows = deploy(args.base, token, "function", FUNCTIONS) + deploy(args.base, token, "tool", TOOLS)
    width = max(len(r[0]) for r in rows)
    failures = 0
    for plugin_id, state, detail in rows:
        if state in ("FAILED", "MISSING"):
            failures += 1
        print(f"  {plugin_id.ljust(width)}  {state:<8} {detail}")

    if failures:
        print(f"\n{failures} plugin(s) did not install.")
        sys.exit(1)
    print("\nAll plugins installed. Select '4CE / TONY (Orchestrator)' in the model picker.")
    print("Enable the tools on that model under Workspace -> Models to let JARVIS call them.")


if __name__ == "__main__":
    main()
