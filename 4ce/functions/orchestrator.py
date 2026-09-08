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
        show_reasoning: bool = Field(
            default=True,
            description="Expose each agent's full reasoning and output as expandable sections.",
        )
        show_model_thinking: bool = Field(
            default=True,
            description="Include the model's own <think> content in each agent's reasoning section.",
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
        steps: list[dict] = []

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
        steps.append({
            "agent": "TONY",
            "label": "classification and routing",
            "model": "deterministic signal match",
            "seconds": 0.0,
            "thinking": "",
            "text": (
                f"**Task type:** `{task_type}`\n\n"
                f"**Signals matched:** {', '.join(signals) if signals else 'none — used the default route'}\n\n"
                f"**Model selected:** `{model_id}`\n\n"
                f"**Reason:** {rationale}\n\n"
                f"**Candidates considered:** "
                + ", ".join(f"`{k}` → `{v}`" for k, v in {
                    "code": self.valves.coding_model,
                    "vision": self.valves.vision_model,
                    "document/analysis": self.valves.analysis_model,
                }.items())
            ),
        })

        verifier_model = self.valves.verifier_model.strip() or model_id
        challenge: str | None = None
        attempts = 0
        analysis = ""
        deliverable = ""
        verdict: dict = {}

        while True:
            attempts += 1

            round_label = "" if attempts == 1 else f" (attempt {attempts})"

            await _status(__event_emitter__, "friday", "FRIDAY: grounding and analysing")
            friday = await self._agent_call(
                __request__, user, model_id, messages,
                system=_FRIDAY_SYSTEM,
                instruction=_with_challenge(
                    "Analyse the request below. State factual findings drawn only from the "
                    "supplied context, and label every assumption explicitly.\n\n" + prompt,
                    challenge,
                ),
                pass_images=has_image,
            )
            analysis = friday["text"]
            if analysis.startswith(_ERR):
                return analysis
            steps.append({**friday, "agent": "FRIDAY", "label": f"analysis{round_label}"})
            trace.append(f"**FRIDAY** analysed the request in {friday['seconds']:.1f}s.")

            await _status(__event_emitter__, "jarvis", "JARVIS: producing the deliverable")
            jarvis = await self._agent_call(
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
            deliverable = jarvis["text"]
            if deliverable.startswith(_ERR):
                return deliverable
            steps.append({**jarvis, "agent": "JARVIS", "label": f"deliverable{round_label}"})
            trace.append(f"**JARVIS** produced the deliverable in {jarvis['seconds']:.1f}s.")

            if not self.valves.enable_verification:
                verdict = {"status": "SKIPPED", "passed": True, "detail": "Verification disabled in Valves."}
                break

            await _status(__event_emitter__, "ultron", "ULTRON: challenging the result")
            ultron = await self._agent_call(
                __request__, user, verifier_model, messages,
                system=_ULTRON_SYSTEM,
                instruction=(
                    f"ORIGINAL REQUEST\n{prompt}\n\n"
                    f"RESULT TO CHALLENGE\n{deliverable}\n\n"
                    "Reply with PASS or FAIL on the first line, then your concerns."
                ),
            )
            verdict = _parse_verdict(ultron["text"])
            steps.append({
                **ultron,
                "agent": "ULTRON",
                "label": f"verification{round_label} — {verdict['status']}",
            })
            trace.append(f"**ULTRON** returned `{verdict['status']}` in {ultron['seconds']:.1f}s.")

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
        interactive = bool(__event_call__) and bool((__metadata__ or {}).get("session_id"))
        if self.valves.require_approval and not interactive:
            # Never record an approval nobody gave: without a live session there is
            # no one to answer the prompt.
            approval = "NOT OBTAINED — no interactive session to prompt"
            trace.append(
                "**HUMAN** approval is required but no interactive session was available, "
                "so this result is unapproved and must not be treated as released."
            )
        elif self.valves.require_approval:
            await _status(__event_emitter__, "approval", "Awaiting human approval")
            # An 'input' prompt rather than a yes/no confirmation, deliberately.
            # The confirm dialog treats a stray Enter as approval, which would let
            # an unreviewed deliverable through by reflex. Requiring the word to be
            # typed makes the gate fail closed: anything else withholds the result.
            response = await __event_call__(
                {
                    "type": "input",
                    "data": {
                        "title": "4CE — human approval required",
                        "message": (
                            f"ULTRON verdict: {verdict.get('status', 'UNKNOWN')}"
                            f" · {task_type} · {model_id}\n\n"
                            "Type APPROVE to release this deliverable. "
                            "Anything else, or an empty box, withholds it."
                        ),
                        "placeholder": "APPROVE",
                    },
                }
            )
            decision = response if isinstance(response, str) else ""
            approved = decision.strip().lower() in ("approve", "approved")
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
                    + _provenance(
                        steps, task_type, signals, model_id, rationale, verdict, "rejected",
                        time.monotonic() - started, attempts, self.valves.show_model_thinking,
                        trace if self.valves.show_trace else [],
                    )
                )

        await _status(__event_emitter__, "done", "Complete", done=True)

        if not self.valves.show_reasoning:
            return deliverable
        return deliverable + "\n\n" + _provenance(
            steps, task_type, signals, model_id, rationale, verdict, approval,
            time.monotonic() - started, attempts, self.valves.show_model_thinking,
            trace if self.valves.show_trace else [],
        )

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
        started = time.monotonic()
        try:
            response = await generate_chat_completion(request, form_data=payload, user=user, bypass_filter=True)
        except Exception as exc:
            return _step(f"{_ERR} local model call to '{model}' failed: {exc}", "", model, started)
        raw, separate_reasoning = _response_parts(response)
        if not raw.strip() and not separate_reasoning.strip():
            return _step(f"{_ERR} local model '{model}' returned an empty response.", "", model, started)
        answer, inline_thinking = _split_thinking(raw.strip())
        thinking = "\n\n".join(t for t in (separate_reasoning.strip(), inline_thinking) if t)
        return _step(answer or raw.strip(), thinking, model, started)


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


def _step(text: str, thinking: str, model: str, started: float) -> dict:
    return {"text": text, "thinking": thinking, "model": model, "seconds": time.monotonic() - started}


def _split_thinking(raw: str) -> tuple[str, str]:
    """Separate a reasoning model's <think> content from its actual answer."""
    thoughts: list[str] = []
    for open_tag, close_tag in (("<think>", "</think>"), ("<thinking>", "</thinking>")):
        while open_tag in raw:
            head, _, rest = raw.partition(open_tag)
            thought, closed, tail = rest.partition(close_tag)
            if not closed:
                # Unterminated block: treat the remainder as thinking rather than
                # letting a raw tag leak into the deliverable.
                thoughts.append(thought.strip())
                raw = head
                break
            thoughts.append(thought.strip())
            raw = head + tail
    return raw.strip(), "\n\n".join(t for t in thoughts if t).strip()


def _provenance(steps: list[dict], task_type: str, signals: list[str], model_id: str,
                rationale: str, verdict: dict, approval: str, elapsed: float,
                attempts: int, include_thinking: bool, trace: list[str]) -> str:
    """A compact provenance table plus the reasoning behind each decision."""
    timings = " · ".join(
        f"{s['agent'].title()} {s['seconds']:.0f}s" for s in steps if s.get("seconds")
    )
    status = verdict.get("status", "n/a")
    rows = [
        ("Task type", f"`{task_type}`" + (f" — matched: {', '.join(signals)}" if signals else " — no strong signal")),
        ("Model routed", f"`{model_id}` — {rationale}"),
        ("Verification", f"ULTRON **{status}**" + (f" after {attempts} attempts" if attempts > 1 else "")),
        ("Human approval", approval.capitalize()),
        ("Elapsed", f"{elapsed:.0f}s" + (f" · {timings}" if timings else "")),
        ("Inference", "Local open-weight models · 0 external API calls"),
    ]
    table = ["| Stage | Detail |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows]

    blocks = ["---", "", "#### 4CE provenance", "", "\n".join(table)]

    for step in steps:
        # JARVIS's output is the answer above; repeating it only adds noise unless
        # a replan produced more than one version worth comparing.
        if step["agent"] == "JARVIS" and attempts < 2:
            continue
        if step["agent"] == "TONY":
            continue
        body = [step["text"].strip() or "_no output_"]
        if include_thinking and step.get("thinking"):
            body += ["", "**Model's internal reasoning**", "", "> " + step["thinking"].replace("\n", "\n> ")]
        label = f"{step['agent']} — {step['label']}  ·  {step['model']}"
        blocks.append(
            "<details>\n<summary>" + label + "</summary>\n\n" + "\n".join(body) + "\n</details>"
        )

    if trace:
        timeline = "\n".join(f"{i}. {line}" for i, line in enumerate(trace, 1))
        blocks.append("<details>\n<summary>Execution timeline</summary>\n\n" + timeline + "\n</details>")
    return "\n\n".join(blocks)


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


def _response_parts(response: Any) -> tuple[str, str]:
    """Return (content, reasoning) keeping any separately-reported reasoning."""
    payload = response
    if isinstance(payload, list) and len(payload) == 1:
        payload = payload[0]
    if isinstance(payload, dict):
        choices = payload.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            reasoning = message.get("reasoning_content") or message.get("reasoning") or ""
            content = message.get("content") or ""
            if not content and reasoning:
                return reasoning, ""
            return content, reasoning
    return _response_text(response), ""


async def _status(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})


