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
    ("ace_sop_check", "4CE SOP Threshold Check", ROOT / "tools" / "sop_check.py",
     "Assesses inspection readings against SOP thresholds and cites the clause that decided each."),
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


def attach_tools(base, token):
    """Give the orchestrator model the 4CE tools.

    A pipe only receives the tools enabled on its own model record, so without
    this the agent chain silently reasons unaided: no threshold arithmetic, no
    sandboxed execution and no .docx. The record does not exist until something
    writes it, which is why this creates as well as updates.
    """
    tool_ids = [plugin_id for plugin_id, *_ in TOOLS]

    status, body = call(base, "/api/models", token)
    if status != 200 or not body:
        return "SKIPPED", "could not list models"
    served = {m.get("id", ""): m for m in (body.get("data") or [])}
    model_id = next((m for m in served if m.startswith(FUNCTIONS[0][0] + ".")), None)
    if not model_id:
        return "SKIPPED", "orchestrator model not served yet"

    status, existing = call(base, f"/api/v1/models/model?id={model_id}", token)
    existing = existing if status == 200 and isinstance(existing, dict) else {}
    meta = dict(existing.get("meta") or {})
    if sorted(meta.get("toolIds") or []) == sorted(tool_ids):
        return "OK", f"{model_id} already has all {len(tool_ids)} tools"
    meta["toolIds"] = tool_ids

    payload = {
        "id": model_id,
        "name": existing.get("name") or served[model_id].get("name") or FUNCTIONS[0][1],
        "meta": meta,
        "params": existing.get("params") or {},
        "is_active": True,
    }
    status, _ = call(base, "/api/v1/models/model/update", token, payload)
    if status != 200:
        status, _ = call(base, "/api/v1/models/create", token, payload)
    if status != 200:
        return "FAILED", f"could not attach tools (status {status})"
    return "UPDATED", f"{model_id} -> {', '.join(tool_ids)}"


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
    state, detail = attach_tools(args.base, token)
    print(f"  {'tools -> model'.ljust(width)}  {state:<8} {detail}")
    if state == "FAILED":
        print("\nThe agent chain will reason unaided until the tools are attached.")
        sys.exit(1)

    print("\nAll plugins installed. Select '4CE / TONY (Orchestrator)' in the model picker.")


if __name__ == "__main__":
    main()
