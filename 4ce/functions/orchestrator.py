"""
title: 4CE Orchestrator
author: 4CE
version: 0.1.0
description: Sovereign multi-agent orchestrator. TONY classifies and routes, FRIDAY grounds, JARVIS executes, ULTRON verifies, a human approves. All inference stays on locally served open-weight models.
"""

import time
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion

CODE_SIGNALS = (
    "code", "script", "program", "function", "debug", "compile", "refactor",
    "python", "javascript", "sql", "algorithm", "unit test", "traceback",
)
DOCUMENT_SIGNALS = (
    "report", "inspection", "sop", "manual", "approval note", "summarise",
    "summarize", "findings", "drawing", "correspondence", "note sheet",
    "tender", "specification", "procedure", "audit",
)
CALC_SIGNALS = ("calculate", "compute", "thickness", "pressure", "flow rate", "tonnage")


class Pipe:
    class Valves(BaseModel):
        analysis_model: str = Field(
            default="qwen/qwen3-vl-4b",
            description="Model for general reasoning, analysis and document work.",
        )
        coding_model: str = Field(
            default="qwen/qwen3-1.7b",
            description="Model for code generation and debugging tasks.",
        )
        vision_model: str = Field(
            default="qwen/qwen3-vl-4b",
            description="Vision-capable model for scanned documents, drawings and photographs.",
        )
        verifier_model: str = Field(
            default="",
            description="Model ULTRON uses to challenge results. Blank reuses the routed model.",
        )
        enable_verification: bool = Field(
            default=True, description="Run the ULTRON verification pass."
        )
        enable_replan: bool = Field(
            default=True, description="Let TONY replan once when ULTRON fails a result."
        )
        require_approval: bool = Field(
            default=True, description="Require explicit human approval before delivering."
        )
        show_trace: bool = Field(
            default=True, description="Append the execution trace to the delivered answer."
        )

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self) -> list[dict]:
        return [{"id": "tony", "name": "4CE / TONY (Orchestrator)"}]

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __request__: Any,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        __event_call__: Callable[[dict], Awaitable[Any]],
        __metadata__: dict,
        __task__: str | None = None,
    ) -> str:
        if __task__:
            return ""

        started = time.monotonic()
        messages = body.get("messages") or []
        if not messages:
            return "No request received."

        prompt = _text_of(messages[-1])
        has_image = _has_image(messages[-1])
        trace: list[str] = []

        user = await Users.get_user_by_id(__user__["id"])
        if user is None:
            return "4CE could not resolve the requesting user."

        task_type, signals = _classify(prompt, has_image)
        await _status(
            __event_emitter__,
            "tony_plan",
            f"TONY: classified as {task_type.upper()}"
            + (f" ({', '.join(signals)})" if signals else " (no strong signal, defaulting)"),
        )
        trace.append(
            f"**TONY** classified the request as `{task_type}` "
            + (f"on signals: {', '.join(signals)}." if signals else "with no strong signal; used the default route.")
        )

        model_id, rationale = self._route(task_type, __request__, body.get("model", ""))
        if model_id is None:
            return (
                f"4CE could not resolve a local model for a `{task_type}` task. "
                "Check the model names in this function's Valves against the models your "
                "local server actually serves."
            )
        await _status(__event_emitter__, "router", f"ROUTER: selected {model_id} — {rationale}")
        trace.append(f"**ROUTER** selected `{model_id}` — {rationale}")

        verifier_model = self.valves.verifier_model.strip() or model_id
        challenge: str | None = None
        attempts = 0
        analysis = ""
        deliverable = ""
        verdict: dict = {}

        while True:
            attempts += 1

            await _status(__event_emitter__, "friday", "FRIDAY: grounding and analysing")
            analysis = await self._agent_call(
                __request__, user, model_id, messages,
                system=_FRIDAY_SYSTEM,
                instruction=_with_challenge(
                    "Analyse the request below. State factual findings drawn only from the "
                    "supplied context, and label every assumption explicitly.\n\n" + prompt,
                    challenge,
                ),
                pass_images=has_image,
            )
            if analysis.startswith(_ERR):
                return analysis
            trace.append(f"**FRIDAY** produced analysis ({len(analysis)} chars).")

            await _status(__event_emitter__, "jarvis", "JARVIS: producing the deliverable")
            deliverable = await self._agent_call(
                __request__, user, model_id, messages,
                system=_JARVIS_SYSTEM,
                instruction=(
                    f"ORIGINAL REQUEST\n{prompt}\n\n"
                    f"FRIDAY'S ANALYSIS\n{analysis}\n\n"
                    "Produce the finished deliverable the request actually asked for. "
                    "Show working for any calculation. Do not claim you performed an action "
                    "unless it is supported by the analysis above."
                ),
            )
            if deliverable.startswith(_ERR):
                return deliverable
            trace.append(f"**JARVIS** produced the deliverable ({len(deliverable)} chars).")

            if not self.valves.enable_verification:
                verdict = {"status": "SKIPPED", "passed": True, "detail": "Verification disabled in Valves."}
                break

            await _status(__event_emitter__, "ultron", "ULTRON: challenging the result")
            raw_verdict = await self._agent_call(
                __request__, user, verifier_model, messages,
                system=_ULTRON_SYSTEM,
                instruction=(
                    f"ORIGINAL REQUEST\n{prompt}\n\n"
                    f"RESULT TO CHALLENGE\n{deliverable}\n\n"
                    "Reply with PASS or FAIL on the first line, then your concerns."
                ),
            )
            verdict = _parse_verdict(raw_verdict)
            trace.append(f"**ULTRON** returned `{verdict['status']}` — {verdict['detail'][:200]}")

            if verdict["passed"]:
                await _status(__event_emitter__, "ultron", "ULTRON: PASS")
                break

            await _status(__event_emitter__, "ultron", f"ULTRON: FAIL — {verdict['detail'][:80]}")
            if not self.valves.enable_replan or attempts > 1:
                trace.append("**TONY** exhausted the replan budget; delivering with the failure recorded.")
                break

            challenge = verdict["detail"]
            await _status(__event_emitter__, "tony_replan", "TONY: replanning after ULTRON challenge")
            trace.append("**TONY** replanned once and re-ran FRIDAY and JARVIS with the challenge attached.")

        approval = "not required"
        if self.valves.require_approval:
            await _status(__event_emitter__, "approval", "Awaiting human approval")
            approved = await __event_call__(
                {
                    "type": "confirmation",
                    "data": {
                        "title": "4CE — human approval required",
                        "message": (
                            f"ULTRON verdict: {verdict.get('status', 'UNKNOWN')}\n\n"
                            "Approve this deliverable for release?"
                        ),
                    },
                }
            )
            if approved:
                approval = "approved"
                trace.append("**HUMAN** approved the deliverable.")
            else:
                approval = "rejected"
                trace.append("**HUMAN** rejected the deliverable; it was not released.")
                await _status(__event_emitter__, "approval", "Rejected by reviewer", done=True)
                return (
                    "### Deliverable withheld\n\n"
                    "The reviewer rejected this result, so 4CE has not released it.\n\n"
                    + _trace_block(trace, task_type, model_id, verdict, "rejected", started)
                )

        await _status(__event_emitter__, "done", "Complete", done=True)

        if not self.valves.show_trace:
            return deliverable
        return deliverable + "\n\n" + _trace_block(trace, task_type, model_id, verdict, approval, started)

    def _route(self, task_type: str, request: Any, current_model: str) -> tuple[str | None, str]:
        preference = {
            "code": (self.valves.coding_model, "coding task routed to the code-specialised model"),
            "vision": (self.valves.vision_model, "image or scanned input requires a vision-capable model"),
            "document": (self.valves.analysis_model, "document work routed to the general reasoning model"),
            "analysis": (self.valves.analysis_model, "general reasoning task"),
        }[task_type]

        available = _available_models(request)
        wanted = preference[0].strip()

        if not available:
            return (wanted or None), preference[1] + " (model registry unavailable; using the configured name)"

        resolved = _match_model(wanted, available, current_model)
        if resolved:
            suffix = "" if resolved == wanted else f" (resolved '{wanted}' to '{resolved}')"
            return resolved, preference[1] + suffix

        fallback = next((m for m in available if m != current_model), None)
        if fallback:
            return fallback, f"configured model '{wanted}' is not served locally; fell back to '{fallback}'"
        return None, "no local model available"

    async def _agent_call(
        self, request: Any, user: Any, model: str, messages: list[dict],
        system: str, instruction: str, pass_images: bool = False,
    ) -> str:
        content: Any = instruction
        if pass_images:
            parts = [p for p in (messages[-1].get("content") or []) if isinstance(p, dict) and p.get("type") == "image_url"]
            if parts:
                content = [{"type": "text", "text": instruction}, *parts]

        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
            "stream": False,
        }
        try:
            response = await generate_chat_completion(request, form_data=payload, user=user, bypass_filter=True)
        except Exception as exc:
            return f"{_ERR} local model call to '{model}' failed: {exc}"
        text = _response_text(response).strip()
        return text or f"{_ERR} local model '{model}' returned an empty response."


_ERR = "**4CE error:**"

_FRIDAY_SYSTEM = (
    "You are FRIDAY, the analysis agent of a sovereign on-premise AI workbench. "
    "You work only from the context supplied to you. You never claim access to external "
    "systems or the internet. Separate established fact from assumption, and say plainly "
    "when the supplied evidence is insufficient."
)
_JARVIS_SYSTEM = (
    "You are JARVIS, the execution agent of a sovereign on-premise AI workbench. "
    "You turn analysis into a finished, well-structured deliverable. Show your working for "
    "calculations. Never claim to have performed an action you have not actually performed."
)
_ULTRON_SYSTEM = (
    "You are ULTRON, a skeptical verification agent. Challenge the result you are given: "
    "look for unsupported claims, missing steps, arithmetic errors and fabricated detail. "
    "Reply with exactly PASS or FAIL on the first line, then list your concerns."
)


def _classify(prompt: str, has_image: bool) -> tuple[str, list[str]]:
    lowered = prompt.lower()
    if has_image:
        return "vision", ["image attached"]
    hits = [w for w in CODE_SIGNALS if w in lowered]
    if hits:
        return "code", hits[:3]
    hits = [w for w in DOCUMENT_SIGNALS if w in lowered]
    if hits:
        return "document", hits[:3]
    hits = [w for w in CALC_SIGNALS if w in lowered]
    if hits:
        return "analysis", hits[:3]
    return "analysis", []


def _available_models(request: Any) -> list[str]:
    try:
        models = request.app.state.MODELS
        keys = list(models.keys()) if hasattr(models, "keys") else []
    except Exception:
        return []
    return [k for k in keys if "4ce" not in k.lower()]


def _match_model(wanted: str, available: list[str], current: str) -> str | None:
    if not wanted:
        return None
    if wanted in available:
        return wanted
    lowered = wanted.lower()
    for candidate in available:
        if candidate == current:
            continue
        if lowered in candidate.lower() or candidate.lower() in lowered:
            return candidate
    return None


def _text_of(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text")
    return ""


def _has_image(message: dict) -> bool:
    content = message.get("content")
    return isinstance(content, list) and any(
        isinstance(p, dict) and p.get("type") == "image_url" for p in content
    )


def _with_challenge(instruction: str, challenge: str | None) -> str:
    if not challenge:
        return instruction
    return instruction + "\n\nPREVIOUS ATTEMPT WAS REJECTED BY THE VERIFIER FOR:\n" + challenge


def _parse_verdict(raw: str) -> dict:
    text = (raw or "").strip()
    if text.startswith(_ERR):
        return {"status": "ERROR", "passed": False, "detail": text}
    first = text.splitlines()[0].upper() if text else "FAIL"
    passed = first.startswith("PASS")
    return {
        "status": "PASS" if passed else "FAIL",
        "passed": passed,
        "detail": text[:1500] or "Verifier returned nothing.",
    }


def _response_text(response: Any) -> str:
    if isinstance(response, list) and len(response) == 1:
        response = response[0]
    if not isinstance(response, dict):
        body = getattr(response, "body", None)
        if body is None:
            return ""
        try:
            import json
            response = json.loads(body.decode("utf-8", "replace"))
        except Exception:
            return ""
    choices = response.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        return message.get("content") or message.get("reasoning_content") or ""
    return ""


async def _status(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})


def _trace_block(trace: list[str], task_type: str, model_id: str, verdict: dict, approval: str, started: float) -> str:
    lines = "\n".join(f"{i}. {step}" for i, step in enumerate(trace, 1))
    return (
        "<details>\n<summary><b>4CE execution trace</b> — "
        f"{task_type} · {model_id} · ULTRON {verdict.get('status', 'n/a')} · {approval}</summary>\n\n"
        f"{lines}\n\n"
        f"- Elapsed: {time.monotonic() - started:.1f}s\n"
        f"- Inference: local open-weight models only\n"
        f"- External API calls this run: 0\n"
        "</details>"
    )
