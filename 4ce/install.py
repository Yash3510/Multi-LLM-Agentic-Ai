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
import uuid
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
    ("ace_calculations", "4CE Engineering Calculations", ROOT / "tools" / "calculations.py",
     "Works corrosion rate, remaining life and the next inspection in code, every step shown."),
    ("ace_files", "4CE Workspace Files", ROOT / "tools" / "files.py",
     "Reads and writes files in one workspace folder, keeping earlier versions; every access audited."),
    ("ace_sheets", "4CE Spreadsheets", ROOT / "tools" / "sheets.py",
     "Reads workbooks with their formulas and writes changes to a copy as live formulas; never the source."),
]

# The models the orchestrator routes between, and the only ones offered in the
# chat picker. Keep in step with the model valves in functions/orchestrator.py.
# Read from the registry the router reads (models.json), so the models the
# picker offers and the models the router chooses between are one list.
REGISTRY = json.loads((ROOT / "models.json").read_text(encoding="utf-8"))
ROUTED_MODELS = [m["id"] for m in REGISTRY["models"]]

def load_registry(profile: str = "") -> dict:
    """The registry a machine runs: models.json, the laptop profile every
    measurement was taken on, or one of profiles/ for a larger GPU."""
    path = ROOT / "profiles" / f"{profile}.json" if profile else ROOT / "models.json"
    if not path.is_file():
        known = ", ".join(sorted(p.stem for p in (ROOT / "profiles").glob("*.json")))
        raise SystemExit(f"No profile named {profile!r}. The profiles are: {known}.")
    return json.loads(path.read_text(encoding="utf-8"))


# The knowledge base the chain is grounded in, and the documents that make it
# up. Held here so the collection can be rebuilt from the repository: the admin
# "Reset vector DB" action deletes every knowledge record along with the
# vectors, and reindexing afterwards reports success while rebuilding nothing.
KNOWLEDGE_NAME = "Plant SOPs"
KNOWLEDGE_DESCRIPTION = (
    "Standard operating procedures and inspection readings for rotating equipment."
)
KNOWLEDGE_FILES = (
    ROOT / "demo" / "samples" / "SOP-MEC-014_seal_leakage.txt",
    ROOT / "demo" / "samples" / "SOP-MEC-014_readings_P-101B.txt",
)

# Endpoints Open WebUI ships pointing at a third party, on screens this build
# does not use. Blanked on install: an auditor reading the admin settings
# cannot tell an unused vendor default from a live egress path, and should not
# have to. Each entry is (config endpoint, nested path to the URL).
CLOUD_ENDPOINTS = (
    ("/api/v1/images/config", ("IMAGES_OPENAI_API_BASE_URL",)),
    ("/api/v1/images/config", ("IMAGES_EDIT_OPENAI_API_BASE_URL",)),
    ("/api/v1/images/config", ("IMAGES_GEMINI_API_BASE_URL",)),
    ("/api/v1/images/config", ("IMAGES_EDIT_GEMINI_API_BASE_URL",)),
    ("/api/v1/audio/config", ("tts", "OPENAI_API_BASE_URL")),
    ("/api/v1/audio/config", ("tts", "MISTRAL_API_BASE_URL")),
    ("/api/v1/audio/config", ("stt", "OPENAI_API_BASE_URL")),
    ("/api/v1/audio/config", ("stt", "MISTRAL_API_BASE_URL")),
)

# Where each config endpoint accepts its update.
CONFIG_UPDATE_PATHS = {
    "/api/v1/images/config": "/api/v1/images/config/update",
    "/api/v1/audio/config": "/api/v1/audio/config/update",
}


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


# What the empty chat offers a new user. Upstream ships "help me study
# vocabulary" and "ideas for my kids' art", which is the first thing anyone
# sees after signing in to a confidential industrial workbench. Each of these
# exercises a different verified capability instead: grounded retrieval, the
# sandbox and the sovereignty audit.
#
# Three, not four: the suggestion list is capped at max-h-36 with its scrollbar
# hidden, so a fourth is reachable only by scrolling a bar nobody can see - and
# the list is shuffled on every load, so which one vanished would change too.
SUGGESTIONS = [
    {
        "title": ["Check a threshold", "against SOP-MEC-014"],
        "content": "What is the acceptable mechanical seal leakage rate under SOP-MEC-014, "
        "and what must happen if it is exceeded?",
    },
    {
        "title": ["Run code", "in the sealed sandbox"],
        "content": "Write a Python function that returns the median of a list and print it "
        "for [5, 3, 9, 1, 7].",
    },
    {
        "title": ["Audit sovereignty", "of this deployment"],
        "content": "Audit this deployment for anything that could send data off-premise.",
    },
]


def ensure_suggestions(base, token):
    """Put 4CE's own starting prompts on the orchestrator model.

    The empty state reads a model's suggestions before the global defaults, so
    setting them on the record the user actually chats with is enough, and it
    survives restarts because it lives in the database rather than the env.
    """
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
    if meta.get("suggestion_prompts") == SUGGESTIONS:
        return "OK", f"{len(SUGGESTIONS)} starting prompts already set"
    meta["suggestion_prompts"] = SUGGESTIONS

    payload = {
        "id": model_id,
        "name": existing.get("name") or served[model_id].get("name") or FUNCTIONS[0][1],
        "meta": meta,
        "params": existing.get("params") or {},
        "is_active": True,
    }
    status, _ = call(base, "/api/v1/models/model/update", token, payload)
    if status != 200:
        return "FAILED", f"could not set starting prompts (status {status})"
    return "UPDATED", f"{len(SUGGESTIONS)} starting prompts on {model_id}"


def restrict_models(base, token):
    """Serve only the models 4CE routes to, and drop the evaluation arena.

    Whatever the local server happens to have loaded is otherwise offered in
    the chat model picker. On this hardware that has meant an embedding model
    that errors the moment it is selected, and a 27B that will not fit in six
    gigabytes and takes the machine with it. The demonstration also gains a
    stock "Arena Model" that has nothing to do with this system. These live in
    the application database rather than in the repository, so a rebuilt
    database loses them unless this runs again.
    """
    wanted = sorted(ROUTED_MODELS)

    status, config = call(base, "/openai/config", token)
    if status != 200 or not isinstance(config, dict):
        return "SKIPPED", "could not read the model connections"

    configs = dict(config.get("OPENAI_API_CONFIGS") or {})
    urls = config.get("OPENAI_API_BASE_URLS") or []
    changed = False
    for index in range(len(urls)):
        entry = dict(configs.get(str(index)) or {})
        if sorted(entry.get("model_ids") or []) != wanted:
            entry["enable"] = entry.get("enable", True)
            entry["model_ids"] = list(ROUTED_MODELS)
            configs[str(index)] = entry
            changed = True

    if changed:
        payload = dict(config)
        payload["OPENAI_API_CONFIGS"] = configs
        status, _ = call(base, "/openai/config/update", token, payload)
        if status != 200:
            return "FAILED", f"could not restrict the model list (status {status})"

    status, evaluation = call(base, "/api/v1/evaluations/config", token)
    if status == 200 and isinstance(evaluation, dict) and evaluation.get(
        "ENABLE_EVALUATION_ARENA_MODELS"
    ):
        status, _ = call(
            base,
            "/api/v1/evaluations/config",
            token,
            {"ENABLE_EVALUATION_ARENA_MODELS": False},
        )
        if status != 200:
            return "FAILED", f"could not disable the arena model (status {status})"
        changed = True

    if not changed:
        return "OK", f"already serving only {', '.join(ROUTED_MODELS)}"
    return "UPDATED", f"serving only {', '.join(ROUTED_MODELS)}, arena off"


def clear_cloud_endpoints(base, token):
    """Blank the third-party endpoints Open WebUI ships configured.

    Image generation arrives pointing at api.openai.com; speech arrives
    pointing at api.openai.com and api.mistral.ai. Nothing calls any of them -
    the features are off or set to local engines, and there are no keys - but
    they sit in the admin settings of a system whose whole claim is that
    nothing leaves the premises, and an auditor reading that screen has no way
    to tell an unused default from an active egress path. Like the model
    picker, they live in the database rather than the repository, so they come
    back with a rebuild unless this runs.
    """
    cleared, failed = 0, []
    for endpoint in sorted({e for e, _ in CLOUD_ENDPOINTS}):
        paths = [p for e, p in CLOUD_ENDPOINTS if e == endpoint]

        status, config = call(base, endpoint, token)
        if status != 200 or not isinstance(config, dict):
            failed.append(f"{endpoint} unreadable")
            continue

        payload = json.loads(json.dumps(config))
        touched = 0
        for path in paths:
            node = payload
            for key in path[:-1]:
                node = node.get(key) if isinstance(node, dict) else None
                if node is None:
                    break
            if isinstance(node, dict) and node.get(path[-1]):
                node[path[-1]] = ""
                touched += 1

        if not touched:
            continue
        status, _ = call(base, CONFIG_UPDATE_PATHS[endpoint], token, payload)
        if status != 200:
            failed.append(f"{endpoint} rejected ({status})")
            continue
        cleared += touched

    if failed:
        return "FAILED", "; ".join(failed)
    if not cleared:
        return "OK", "no third-party endpoints configured"
    return "UPDATED", f"cleared {cleared} third-party endpoint(s)"



def upload(base, token, path):
    """POST a file as multipart/form-data, using only the standard library."""
    boundary = "----4ce" + uuid.uuid4().hex
    sep = chr(13) + chr(10)
    head = (
        "--" + boundary + sep
        + 'Content-Disposition: form-data; name="file"; filename="'
        + path.name + '"' + sep
        + "Content-Type: text/plain" + sep + sep
    )
    tail = sep + "--" + boundary + "--" + sep
    body = head.encode() + path.read_bytes() + tail.encode()
    request = urllib.request.Request(f"{base.rstrip('/')}/api/v1/files/", data=body)
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, {"detail": exc.read().decode("utf-8", "replace")[:300]}
    except urllib.error.URLError as exc:
        return 0, {"detail": str(exc.reason)}


def ensure_knowledge(base, token):
    """Rebuild the knowledge base the chain is grounded in, if it is gone.

    Grounding is the one failure here that does not announce itself: retrieval
    returns nothing, the agents answer from the model's own memory, and the
    reply still reads like an informed one. It has broken twice - once because
    the collection was never reaching the pipe, and once because "Reset vector
    DB" deletes every knowledge record, after which reindexing reports success
    and rebuilds nothing since there is no record left to reindex.

    So the collection is reconstructible from the repository rather than only
    from a runbook. Existing, intact knowledge is left alone.
    """
    status, body = call(base, "/api/models", token)
    if status != 200 or not body:
        return "SKIPPED", "could not list models"
    model_id = next(
        (m.get("id") for m in (body.get("data") or [])
         if str(m.get("id", "")).startswith(FUNCTIONS[0][0] + ".")),
        None,
    )
    if not model_id:
        return "SKIPPED", "orchestrator model not served yet"

    status, record = call(base, f"/api/v1/models/model?id={model_id}", token)
    record = record if status == 200 and isinstance(record, dict) else {}
    meta = dict(record.get("meta") or {})

    for item in meta.get("knowledge") or []:
        if not isinstance(item, dict):
            continue
        status, detail = call(base, f"/api/v1/knowledge/{item.get('id')}", token)
        if status == 200 and isinstance(detail, dict) and detail.get("name"):
            return "OK", f"'{detail.get('name')}' attached and intact"

    # Reuse a collection that survived but came adrift from the model.
    status, existing = call(base, "/api/v1/knowledge/list", token)
    items = existing.get("items") if isinstance(existing, dict) else existing
    collection = next(
        (k for k in (items or []) if isinstance(k, dict) and k.get("name") == KNOWLEDGE_NAME),
        None,
    )
    rebuilt = False

    if collection is None:
        status, collection = call(
            base, "/api/v1/knowledge/create", token,
            {"name": KNOWLEDGE_NAME, "description": KNOWLEDGE_DESCRIPTION},
        )
        if status != 200 or not isinstance(collection, dict) or not collection.get("id"):
            return "FAILED", f"could not create '{KNOWLEDGE_NAME}' (status {status})"
        rebuilt = True

    knowledge_id = collection.get("id")

    status, stored = call(base, "/api/v1/files/", token)
    by_name = {
        f.get("filename"): f.get("id")
        for f in ((stored or {}).get("items") or [])
        if isinstance(f, dict)
    }

    status, detail = call(base, f"/api/v1/knowledge/{knowledge_id}", token)
    indexed = {
        f.get("filename")
        for f in ((detail or {}).get("files") or [])
        if isinstance(f, dict)
    }

    added, failures = 0, []
    for path in KNOWLEDGE_FILES:
        if path.name in indexed:
            continue
        if not path.exists():
            failures.append(f"{path.name} missing from the repository")
            continue
        file_id = by_name.get(path.name)
        if not file_id:
            status, uploaded = upload(base, token, path)
            if status != 200 or not isinstance(uploaded, dict):
                failures.append(f"{path.name} upload failed ({status})")
                continue
            file_id = uploaded.get("id")
        status, _ = call(
            base, f"/api/v1/knowledge/{knowledge_id}/file/add", token, {"file_id": file_id}
        )
        if status != 200:
            failures.append(f"{path.name} index failed ({status})")
            continue
        added += 1

    if failures:
        return "FAILED", "; ".join(failures)

    status, detail = call(base, f"/api/v1/knowledge/{knowledge_id}", token)
    if status == 200 and isinstance(detail, dict):
        meta["knowledge"] = [detail]
        payload = {
            "id": model_id,
            "name": record.get("name") or FUNCTIONS[0][1],
            "meta": meta,
            "params": record.get("params") or {},
            "is_active": True,
        }
        status, _ = call(base, "/api/v1/models/model/update", token, payload)
        if status != 200:
            return "FAILED", f"could not attach '{KNOWLEDGE_NAME}' (status {status})"

    what = "rebuilt" if rebuilt else "reattached"
    return "UPDATED", f"'{KNOWLEDGE_NAME}' {what}" + (f", {added} file(s) indexed" if added else "")


def push_registry(base, token):
    """Write models.json into the orchestrator's model_registry valve.

    Adding a model is then an entry in that file and a run of this script:
    the router reads capabilities from the valve, and the new model appears in
    every answer's candidate list - chosen, lacking a capability, or not
    served - with no change to code.
    """
    function_id = FUNCTIONS[0][0]
    status, valves = call(base, f"/api/v1/functions/id/{function_id}/valves", token)
    valves = valves if status == 200 and isinstance(valves, dict) else {}
    text = json.dumps(REGISTRY, separators=(",", ":"), ensure_ascii=False)
    profile = REGISTRY.get("profile") or {}
    summary = (
        f"{profile.get('name', 'default')}: {len(ROUTED_MODELS)} models, "
        f"{len(REGISTRY.get('routing') or {})} task routes"
        + ("" if profile.get("measured", True) else " (planned, not measured here)")
    )
    # A profile also sets the valves that suit its GPU: reply budgets, image
    # sizes, retrieval depth. Switching back to the laptop sets them back.
    tuned = {k: v for k, v in (profile.get("valves") or {}).items()}
    if valves.get("model_registry") == text and all(valves.get(k) == v for k, v in tuned.items()):
        return "OK", summary
    valves["model_registry"] = text
    valves.update(tuned)
    status, _ = call(base, f"/api/v1/functions/id/{function_id}/valves/update", token, valves)
    if status != 200:
        return "FAILED", f"could not write the model_registry valve (status {status})"
    return "UPDATED", summary


def main():
    parser = argparse.ArgumentParser(description="Install the 4CE plugin set.")
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--email", default="admin@4ce.local")
    parser.add_argument("--password", default="4ce-demo-password")
    parser.add_argument("--name", default="4CE Administrator")
    parser.add_argument("--profile", default="",
                        help="a hardware profile from 4ce/profiles/, e.g. workstation-24gb; blank uses models.json")
    args = parser.parse_args()
    if args.profile:
        global REGISTRY, ROUTED_MODELS
        REGISTRY = load_registry(args.profile)
        ROUTED_MODELS = [m["id"] for m in REGISTRY["models"]]

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
    picker_state, picker_detail = restrict_models(args.base, token)
    print(f"  {'model picker'.ljust(width)}  {picker_state:<8} {picker_detail}")
    registry_state, registry_detail = push_registry(args.base, token)
    print(f"  {'model registry'.ljust(width)}  {registry_state:<8} {registry_detail}")

    prompts_state, prompts_detail = ensure_suggestions(args.base, token)
    print(f"  {'starting prompts'.ljust(width)}  {prompts_state:<8} {prompts_detail}")
    egress_state, egress_detail = clear_cloud_endpoints(args.base, token)
    print(f"  {'cloud endpoints'.ljust(width)}  {egress_state:<8} {egress_detail}")
    knowledge_state, knowledge_detail = ensure_knowledge(args.base, token)
    print(f"  {'knowledge base'.ljust(width)}  {knowledge_state:<8} {knowledge_detail}")
    if state == "FAILED":
        print("\nThe agent chain will reason unaided until the tools are attached.")
        sys.exit(1)

    print("\nAll plugins installed. Select '4CE / TONY (Orchestrator)' in the model picker.")


if __name__ == "__main__":
    main()
