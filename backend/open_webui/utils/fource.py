"""4CE: how the latest run in a chat ended, for the sidebar's chat list.

Read from the chat itself - the latest answer on the current branch, its
status history and its ```4ce-receipt block - so it needs nothing the
orchestrator does not already write. One of:

- "released": you approved it;
- "withheld": you rejected it, or no reviewer answered;
- "stopped": the run failed, was stopped, or was cut off;
- "direct": a direct reply, which never goes through the chain;
- "done": a finished run with no sign-off asked for;
- "": not a 4CE answer, or still running (the list marks running chats).
"""

import json
import re

_RECEIPT = re.compile(r"```4ce-receipt\s*\n(.*?)\n```", re.S)


def fource_outcome(chat: dict | None) -> str:
    history = (chat or {}).get("history") or {}
    messages = history.get("messages") or {}
    message = messages.get(history.get("currentId") or "")
    # The latest answer on the branch in view: a question waiting on its
    # answer points back to the answer before it.
    seen = set()
    while message and message.get("role") != "assistant" and message.get("id") not in seen:
        seen.add(message.get("id"))
        message = messages.get(message.get("parentId") or "")
    if not message or not str(message.get("model") or "").startswith("ace_orchestrator"):
        return ""
    if not message.get("done"):
        return ""

    content = str(message.get("content") or "")
    statuses = [s for s in (message.get("statusHistory") or []) if isinstance(s, dict)]
    actions = {s.get("action") for s in statuses}
    if content.lstrip().startswith("**4CE error:**") or actions & {"error", "stopped"}:
        return "stopped"
    # Finished with its last status still open: cut off (a restart, a reload).
    if statuses and statuses[-1].get("done") is False:
        return "stopped"
    if "chat" in actions:
        return "direct"

    match = _RECEIPT.search(content)
    if match:
        try:
            approval = str(json.loads(match.group(1)).get("approval") or "").lower()
        except (ValueError, AttributeError):
            approval = ""
        if approval == "approved":
            return "released"
        if approval.startswith("rejected") or "not obtained" in approval:
            return "withheld"
    if "### Deliverable withheld" in content:
        return "withheld"
    return "done"
