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

GREETINGS = {
    "hi", "hello", "hey", "yo", "hiya", "howdy", "hola", "namaste",
    "morning", "afternoon", "evening", "greetings",
    "good morning", "good afternoon", "good evening", "good day",
}
COURTESIES = {
    "thanks", "thank you", "thankyou", "ta", "cheers", "ok", "okay", "k", "cool",
    "nice", "great", "perfect", "got it", "understood", "sure", "yes", "no",
    "bye", "goodbye", "see you", "good night", "test", "testing",
}
META_QUESTIONS = (
    "who are you", "what are you", "what can you do", "what do you do",
    "how do you work", "what is 4ce", "who made you", "introduce yourself",
    "what models do you", "which models do you", "are you online", "are you there",
)


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
        chat_model: str = Field(
            default="qwen/qwen3-1.7b",
            description="Small, fast model for greetings and questions about the assistant. These answer directly and never enter the agent chain.",
        )
        orchestrate_small_talk: bool = Field(
            default=False,
            description="Send greetings and small talk through the full agent chain as well. Off by default: verifying and seeking human approval for 'hello' wastes a minute and devalues the approval gate.",
        )
        friday_model: str = Field(
            default="",
            description="AGENT OVERRIDE — model FRIDAY uses to ground and analyse. Blank follows the routed model.",
        )
        jarvis_model: str = Field(
            default="",
            description="AGENT OVERRIDE — model JARVIS uses to produce the deliverable. Blank follows the routed model.",
        )
        ultron_model: str = Field(
            default="",
            description="AGENT OVERRIDE — model ULTRON uses to challenge the result. Blank follows the routed model. A different model here gives genuinely independent verification.",
        )
        vision_max_edge: int = Field(
            default=900,
            description="Longest edge, in pixels, an image is downscaled to before it reaches the vision model. Smaller is markedly faster on modest GPUs. Set 0 to send images untouched.",
        )
        max_tokens: int = Field(
            default=900,
            description="Upper bound on each agent's reply. Keeps a single turn predictable on modest hardware; a reasoning model left unbounded can run for minutes. Set 0 for no limit.",
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

        if task_type == "chat" and not self.valves.orchestrate_small_talk:
            await _status(__event_emitter__, "chat", "Answering directly", done=True)
            reply = await self._agent_call(
                __request__, user, model_id, messages,
                system=_TONY_CHAT_SYSTEM, instruction=prompt,
            )
            if reply["text"].startswith(_ERR):
                return reply["text"]
            note = (
                f"\n\n<sub>4CE · direct reply · `{model_id}` · {reply['seconds']:.1f}s · "
                "no agent chain, no approval needed for conversation</sub>"
            )
            return reply["text"] + (note if self.valves.show_trace else "")

        available = _available_models(__request__)
        agent_models = {
            "FRIDAY": self._agent_model(self.valves.friday_model, model_id, available),
            "JARVIS": self._agent_model(self.valves.jarvis_model, model_id, available),
            "ULTRON": self._agent_model(self.valves.ultron_model, model_id, available),
        }
        overrides = {a: m for a, m in agent_models.items() if m != model_id}
        if overrides:
            trace.append(
                "**TONY** applied per-agent model overrides: "
                + ", ".join(f"{a} → `{m}`" for a, m in overrides.items())
            )
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
                __request__, user, agent_models["FRIDAY"], messages,
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
                __request__, user, agent_models["JARVIS"], messages,
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
                __request__, user, agent_models["ULTRON"], messages,
                system=_ULTRON_SYSTEM,
                instruction=(
                    f"ORIGINAL REQUEST\n{prompt}\n\n"
                    + (
                        "SOURCE NOTE: the request carried a scanned document or image. FRIDAY "
                        "read it; you cannot see it. Judge internal consistency, arithmetic and "
                        "whether the result claims more than an extraction can support. Do NOT "
                        "fail it merely because you cannot inspect the source yourself.\n\n"
                        if has_image else ""
                    )
                    + f"RESULT TO CHALLENGE\n{deliverable}\n\n"
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
                        trace if self.valves.show_trace else [], agent_models,
                    )
                )

        await _status(__event_emitter__, "done", "Complete", done=True)

        if not self.valves.show_reasoning:
            return deliverable
        return deliverable + "\n\n" + _provenance(
            steps, task_type, signals, model_id, rationale, verdict, approval,
            time.monotonic() - started, attempts, self.valves.show_model_thinking,
            trace if self.valves.show_trace else [], agent_models,
        )

    def _agent_model(self, override: str, routed: str, available: list[str]) -> str:
        """An agent's assigned model, falling back to the routed one."""
        wanted = (override or "").strip()
        if not wanted:
            return routed
        return _match_model(wanted, available, "") or routed

    def _route(self, task_type: str, request: Any, current_model: str) -> tuple[str | None, str]:
        preference = {
            "chat": (self.valves.chat_model, "conversational message answered directly by the small model"),
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
                limit = self.valves.vision_max_edge
                parts = [_shrink_image(p, limit) for p in parts] if limit else parts
                content = [{"type": "text", "text": instruction}, *parts]

        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
            "stream": False,
        }
        if self.valves.max_tokens:
            payload["max_tokens"] = self.valves.max_tokens
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
_TONY_CHAT_SYSTEM = (
    "You are TONY, the coordinator of 4CE — a sovereign, on-premise AI workbench for "
    "confidential industrial work. You run entirely on local open-weight models with no "
    "external connection. You coordinate three agents: FRIDAY grounds and analyses, "
    "JARVIS produces deliverables, and ULTRON verifies them before a human approves. "
    "This message is conversation rather than a work request, so answer it directly, "
    "warmly and briefly. Do not invent capabilities and do not claim to have performed "
    "any action."
)
_ULTRON_SYSTEM = (
    "You are ULTRON, a skeptical verification agent. Challenge the result you are given: "
    "look for unsupported claims, missing steps, arithmetic errors and fabricated detail. "
    "Reply with exactly PASS or FAIL on the first line, then list your concerns."
)


def _conversational(prompt: str) -> str | None:
    """Identify small talk so it never enters the approval-controlled flow.

    Deliberately strict: it only matches messages that are *entirely* social or
    about the assistant itself. Anything that looks like work - even a short sum -
    still earns the full agent chain, because that is what gets verified.
    """
    import re

    text = re.sub(r"[^a-z0-9\s]", " ", prompt.lower())
    text = " ".join(text.split())
    if not text:
        return None
    words = text.split()
    if len(words) > 8:
        return None
    if text in GREETINGS or text in COURTESIES:
        return text
    if words[0] in GREETINGS and len(words) <= 5:
        return words[0]
    for phrase in META_QUESTIONS:
        if phrase in text:
            return phrase
    return None


def _classify(prompt: str, has_image: bool) -> tuple[str, list[str]]:
    lowered = prompt.lower()
    if has_image:
        return "vision", ["image attached"]
    small_talk = _conversational(prompt)
    if small_talk:
        return "chat", [f"conversational: '{small_talk}'"]
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


def _shrink_image(part: dict, max_edge: int) -> dict:
    """Downscale an inline image. A full-page scan costs minutes on a modest GPU."""
    url = (part.get("image_url") or {}).get("url", "")
    if not url.startswith("data:image") or "base64," not in url:
        return part
    try:
        import base64
        import io

        from PIL import Image

        header, encoded = url.split("base64,", 1)
        image = Image.open(io.BytesIO(base64.b64decode(encoded)))
        if max(image.size) <= max_edge:
            return part
        image.thumbnail((max_edge, max_edge), Image.LANCZOS)
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, "JPEG", quality=88)
        shrunk = base64.b64encode(buffer.getvalue()).decode("ascii")
        return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + shrunk}}
    except Exception:
        # Never fail the turn over a resize; send the original instead.
        return part


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
                attempts: int, include_thinking: bool, trace: list[str],
                agent_models: dict) -> str:
    """A compact provenance table plus the reasoning behind each decision."""
    timings = " · ".join(
        f"{s['agent'].title()} {s['seconds']:.0f}s" for s in steps if s.get("seconds")
    )
    status = verdict.get("status", "n/a")
    rows = [
        ("Task type", f"`{task_type}`" + (f" — matched: {', '.join(signals)}" if signals else " — no strong signal")),
        ("Model routed", f"`{model_id}` — {rationale}"),
        ("Agents", " · ".join(f"{a} `{m}`" for a, m in agent_models.items())),
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


