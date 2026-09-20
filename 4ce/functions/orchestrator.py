"""
title: 4CE Orchestrator
author: 4CE
version: 0.1.0
description: Sovereign multi-agent orchestrator. TONY classifies and routes, FRIDAY grounds, JARVIS executes, ULTRON verifies, a human approves. All inference stays on locally served open-weight models.
"""

import ast
import asyncio
import inspect
import re
import time
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from open_webui.models.chats import Chats
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
AUDIT_SIGNALS = (
    "prove nothing leaves", "leaves the premises", "leave the premises",
    "sovereignty", "sovereign", "audit the running", "audit the configuration",
    "external call", "air gap", "air-gapped", "offline mode", "telemetry",
    "data leaving", "phone home",
)
CALC_SIGNALS = ("calculate", "compute", "thickness", "pressure", "flow rate", "tonnage")

# Task types a knowledge base can actually inform. Greetings and code do not
# become better for having plant procedures pasted in front of them.
RETRIEVING_TASKS = frozenset({"document", "vision", "analysis"})

GREETINGS = {
    "hi", "hello", "hey", "yo", "hiya", "howdy", "hola", "namaste",
    "morning", "afternoon", "evening", "greetings",
    "good morning", "good afternoon", "good evening", "good day",
}
COURTESIES = {
    "thanks", "thank you", "thankyou", "ta", "cheers", "ok", "okay", "k", "cool",
    "nice", "great", "perfect", "got it", "understood", "sure", "yes", "no",
    "bye", "goodbye", "see you", "good night", "test", "testing",
    # Short fillers said out loud while presenting. Without these a throwaway
    # remark is classified as work: it convenes the chain, spends a minute and
    # then asks a human to approve whatever it invented from two words.
    "and again", "again", "once more", "go on", "carry on", "continue",
    "next", "same again", "one more", "and", "so", "right", "fine", "alright",
    "indeed", "exactly", "correct", "wonderful", "excellent", "brilliant",
    "lovely", "hmm", "hm", "ah", "oh", "i see", "makes sense", "noted",
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
        independent_verification: bool = Field(
            default=True,
            description=(
                "When ULTRON has no model of its own, give it a different model from "
                "JARVIS. Verification on the same weights reproduces the same blind spot."
            ),
        )
        ultron_model: str = Field(
            default="",
            description="AGENT OVERRIDE — model ULTRON uses to challenge the result. Blank follows the routed model. A different model here gives genuinely independent verification.",
        )
        retrieval_k: int = Field(
            default=4,
            description="Passages retrieved from an attached knowledge base and given to FRIDAY.",
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
            # No angle brackets: the valve panel renders descriptions as HTML,
            # so a literal <think> is parsed as a tag and silently dropped,
            # leaving "the model's own content" and no hint of what is meant.
            description="Include the model's own think-block content in each agent's reasoning section.",
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
        __tools__: dict | None = None,
        __task__: str | None = None,
    ) -> str:
        """Run the chain, and leave a record behind if the reviewer stops it.

        A pipe hands back a single string at the end, so a cancelled run has
        nothing to persist: the bubble spins forever and the reply disappears
        on reload. The stop is still honoured and the work is abandoned, but
        the turn says so rather than vanishing.
        """
        trace: list[str] = []
        steps: list[dict] = []
        try:
            answer = await self._run_chain(
                body,
                __user__,
                __request__,
                __event_emitter__,
                __event_call__,
                __metadata__,
                __tools__,
                __task__,
                trace,
                steps,
            )
            await self._report_usage(__metadata__, steps)
            return answer
        except asyncio.CancelledError:
            # One shield around both writes, not two. Awaiting a shield in an
            # already-cancelled task re-raises CancelledError as soon as the
            # inner coroutine finishes, so a second shielded await after it is
            # never reached and the stopped run records no token cost.
            await asyncio.shield(
                self._record_stopped_turn(__metadata__, __event_emitter__, trace, steps)
            )
            raise

    async def _record_stopped_turn(
        self,
        metadata: dict,
        emitter: Callable[[dict], Awaitable[None]] | None,
        trace: list[str],
        steps: list[dict],
    ) -> None:
        """Everything a stopped run still owes: the record, and what it spent."""
        await self._record_stop(metadata, emitter, trace, steps)
        await self._report_usage(metadata, steps)

    async def _report_usage(self, metadata: dict, steps: list[dict]) -> None:
        """Record the turn's real token cost against the stored message.

        Every agent call is made inside the pipe, so the platform only ever
        sees one opaque turn. It reads usage off the pipe's return value, and a
        pipe returns a string, so nothing is recorded: the usage and analytics
        pages report zero tokens against a system that has just run several
        models. Writing the total onto the message is the same route the
        stopped-run record uses, and the platform's own later write omits the
        key rather than clearing it.
        """
        usage = _usage_total(steps)
        chat_id = (metadata or {}).get("chat_id")
        message_id = (metadata or {}).get("message_id")
        if not usage or not chat_id or not message_id:
            return
        try:
            await Chats.upsert_message_to_chat_by_id_and_message_id(
                chat_id, message_id, {"usage": usage}
            )
        except Exception:
            # Accounting is not worth failing a delivered answer over.
            pass

    async def _record_stop(
        self,
        metadata: dict,
        emitter: Callable[[dict], Awaitable[None]] | None,
        trace: list[str],
        steps: list[dict],
    ) -> None:
        """Write the turn a stopped reviewer would otherwise be left without."""
        done = [s for s in steps if s.get("agent") not in (None, "TONY")]
        lines = [
            "### Stopped",
            "",
            "The run was stopped before it produced a deliverable. Nothing was "
            "released and nothing was approved.",
        ]
        if done:
            lines += [
                "",
                "Completed before the stop: "
                + ", ".join(f"{s['agent']} ({s['label']})" for s in done)
                + ".",
            ]
        if trace:
            lines += ["", "<details>", "<summary>Execution timeline</summary>", ""]
            lines += [f"{i}. {line}" for i, line in enumerate(trace, 1)]
            lines += ["", "</details>"]
        content = "\n".join(lines)

        # Update the open bubble, then the stored chat, so the turn is right
        # both on screen and after a reload. Either may fail mid-cancellation.
        try:
            if emitter:
                # Close the status line first. It is left mid-sentence on the
                # agent that was running, so without this the bubble reads
                # "JARVIS: producing the deliverable" directly above a message
                # saying the run was stopped and produced nothing.
                await _status(emitter, "stopped", "Stopped by reviewer", done=True)
                await emitter({"type": "replace", "data": {"content": content}})
        except Exception:
            pass
        chat_id = (metadata or {}).get("chat_id")
        message_id = (metadata or {}).get("message_id")
        if not chat_id or not message_id:
            return
        try:
            await Chats.upsert_message_to_chat_by_id_and_message_id(
                chat_id, message_id, {"content": content, "done": True}
            )
        except Exception:
            pass

    async def _run_chain(
        self,
        body: dict,
        __user__: dict,
        __request__: Any,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        __event_call__: Callable[[dict], Awaitable[Any]],
        __metadata__: dict,
        __tools__: dict | None,
        __task__: str | None,
        trace: list[str],
        steps: list[dict],
    ) -> str:
        if __task__:
            return ""

        started = time.monotonic()
        messages = body.get("messages") or []
        if not messages:
            return "No request received."

        prompt = _text_of(messages[-1])
        has_image = _has_image(messages[-1])
        retrieved = _retrieved_context(messages)
        grounding = _grounding_text(messages)

        user = await Users.get_user_by_id(__user__["id"])
        if user is None:
            return "4CE could not resolve the requesting user."

        task_type, signals = _classify(prompt, has_image)

        # Retrieve after classifying, and only where documents can help. An
        # attached knowledge base is queried on every turn otherwise, so a
        # greeting or a request for a median function arrives carrying several
        # thousand characters of pump procedures: slower on a small card, and
        # provenance that claims a median was grounded in plant SOPs.
        if task_type in RETRIEVING_TASKS:
            passages = await self._retrieve(__request__, user, __metadata__, prompt)
            if passages:
                retrieved = f"{retrieved}\n\n{passages}".strip() if retrieved else passages
                grounding = f"{grounding}\n\n{passages}".strip() if grounding else passages

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
            # Recorded even though this path shows no provenance table: it is
            # still a model call, and the turn's token accounting reads steps.
            steps.append({**reply, "agent": "TONY", "label": "direct reply"})
            # Plain markdown, not HTML: the renderer special-cases only a handful
            # of tags and prints every other one as literal text.
            note = (
                f"\n\n*4CE · direct reply · `{model_id}` · {reply['seconds']:.1f}s · "
                "no agent chain, no approval needed for conversation*"
            )
            return reply["text"] + (note if self.valves.show_trace else "")

        available = _available_models(__request__)
        agent_models = {
            "FRIDAY": self._agent_model(self.valves.friday_model, model_id, available),
            "JARVIS": self._agent_model(self.valves.jarvis_model, model_id, available),
            "ULTRON": self._agent_model(
                self.valves.ultron_model, model_id, available, independent=True
            ),
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
        tools_used: list[str] = []

        if not __tools__:
            trace.append(
                "**TONY** found no tools attached to this model, so the agents reasoned "
                "unaided. Attach the 4CE tools to this model under Workspace to ground "
                "threshold checks, code execution and deliverables."
            )

        # Sovereignty is evidenced, not narrated: read the running configuration
        # rather than letting a model describe the configuration it imagines.
        audit = ""
        if _wants_audit(prompt):
            await _status(
                __event_emitter__, "tool", "TOOL: auditing the running configuration"
            )
            audit = await self._use_tool(__tools__, "verify_sovereignty")
            if audit and not audit.startswith(_ERR):
                tools_used.append("verify_sovereignty")
                steps.append({
                    "agent": "TOOL",
                    "label": "sovereignty audit",
                    "model": "deterministic configuration read",
                    "seconds": 0.0,
                    "thinking": "",
                    "text": audit,
                })
                trace.append(
                    "**TOOL** `verify_sovereignty` read the live configuration."
                )
            else:
                audit = ""

        while True:
            attempts += 1

            round_label = "" if attempts == 1 else f" (attempt {attempts})"

            await _status(__event_emitter__, "friday", "FRIDAY: grounding and analysing")
            friday = await self._agent_call(
                __request__, user, agent_models["FRIDAY"], messages,
                system=_FRIDAY_SYSTEM,
                instruction=_with_challenge(
                    "Analyse the request below. State factual findings drawn only from the "
                    "supplied context, and label every assumption explicitly."
                    + (
                        "\n\nSUPPLIED CONTEXT - passages retrieved from the local "
                        "knowledge base, and any standing instruction for this workspace. "
                        "Treat this as the supplied context and cite it where you rely on "
                        "it:\n"
                        + retrieved
                        if retrieved
                        else ""
                    )
                    + "\n\nREQUEST\n"
                    + prompt,
                    challenge,
                ),
                pass_images=has_image,
            )
            analysis = friday["text"]
            if analysis.startswith(_ERR):
                return analysis
            steps.append({**friday, "agent": "FRIDAY", "label": f"analysis{round_label}"})
            trace.append(f"**FRIDAY** analysed the request in {friday['seconds']:.1f}s.")

            # Threshold arithmetic belongs to the authored rule pack, not to a model.
            # ULTRON reading 6.2 mm against a 6.0 mm retirement limit as a breach is
            # precisely the failure this removes.
            # Readings come from the request, or from the page in a vision task.
            # Deciding from FRIDAY's prose instead makes it fire on anything that
            # happens to mention a number - a sovereignty audit reporting "11 of
            # 11" should not produce an SOP assessment row.
            sop = ""
            assessable = task_type == "vision" or _has_readings(prompt)
            if task_type in ("document", "analysis", "vision") and assessable:
                await _status(
                    __event_emitter__,
                    "tool",
                    "TOOL: comparing readings against the SOP thresholds",
                )
                sop = await self._use_tool(
                    __tools__,
                    "check_sop_thresholds",
                    readings=prompt + "\n\n" + analysis,
                )
                if sop and not sop.startswith(_ERR):
                    if "check_sop_thresholds" not in tools_used:
                        tools_used.append("check_sop_thresholds")
                    steps.append({
                        "agent": "TOOL",
                        "label": f"SOP threshold check{round_label}",
                        "model": "deterministic rule pack",
                        "seconds": 0.0,
                        "thinking": "",
                        "text": sop,
                    })
                    trace.append(
                        "**TOOL** `check_sop_thresholds` compared the readings against the "
                        "authored rule pack and cited the deciding clause."
                    )
                else:
                    sop = ""

            grounded = ""
            if audit:
                grounded += (
                    "\n\nSOVEREIGNTY AUDIT (read from the running configuration; "
                    "authoritative)\n" + audit
                )
            if sop:
                grounded += (
                    "\n\nSOP THRESHOLD ASSESSMENT (deterministic rule pack; "
                    "authoritative)\n" + sop
                )

            await _status(__event_emitter__, "jarvis", "JARVIS: producing the deliverable")
            jarvis = await self._agent_call(
                __request__, user, agent_models["JARVIS"], messages,
                system=_JARVIS_SYSTEM,
                instruction=(
                    f"ORIGINAL REQUEST\n{prompt}\n\n"
                    f"FRIDAY'S ANALYSIS\n{analysis}"
                    + grounded
                    + (
                        "\n\nPut every line of code inside a fenced ```python block. "
                        "This code will be executed. If the request calls for a file - "
                        "a spreadsheet, a chart, an export - write it into the directory "
                        "/output, which is returned to the user. Nowhere else is writable."
                        if task_type == "code"
                        else ""
                    )
                    + "\n\nProduce the finished deliverable the request actually asked "
                    "for. Show working for any calculation. Do not claim you performed an "
                    "action unless it is supported by the analysis above. Where a section "
                    "above is marked authoritative, quote its verdicts as they stand and "
                    "do not recompute them."
                ),
            )
            deliverable = jarvis["text"]
            if deliverable.startswith(_ERR):
                return deliverable
            steps.append({**jarvis, "agent": "JARVIS", "label": f"deliverable{round_label}"})
            trace.append(f"**JARVIS** produced the deliverable in {jarvis['seconds']:.1f}s.")

            # Generated code is run, not admired. The real output is appended so
            # ULTRON and the reviewer judge what actually executed.
            if task_type == "code":
                code = _extract_python(deliverable)
                if code:
                    await _status(
                        __event_emitter__,
                        "tool",
                        "TOOL: executing the generated code in the sandbox",
                    )
                    execution = await self._use_tool(__tools__, "run_python", code=code)
                    if execution and not execution.startswith(_ERR):
                        if "run_python" not in tools_used:
                            tools_used.append("run_python")
                        steps.append({
                            "agent": "TOOL",
                            "label": f"sandboxed execution{round_label}",
                            "model": "container, no network",
                            "seconds": 0.0,
                            "thinking": "",
                            "text": execution,
                        })
                        trace.append(
                            "**TOOL** `run_python` executed the generated code in a "
                            "network-less container and returned its real output."
                        )
                        deliverable += (
                            "\n\n---\n\n**Sandboxed execution result**\n\n"
                            + execution
                        )

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
                    + (
                        "AUTHORITATIVE FINDINGS — produced by deterministic tools, not by "
                        "a model. Treat them as correct. Do not re-derive them and do not "
                        "fail the result for disagreeing with them."
                        + grounded
                        + "\n\n"
                        if grounded
                        else ""
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
        waited = 0.0
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
            # The reviewer's thinking time is not the system's running time.
            # Counted together, a 40-second task reports two minutes because
            # somebody read it before approving.
            asked_at = time.monotonic()
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
            waited = time.monotonic() - asked_at
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
                        time.monotonic() - started - waited, attempts, self.valves.show_model_thinking,
                        trace if self.valves.show_trace else [], agent_models, tools_used, grounding,
                    )
                )

        # Whatever the request actually asked for, in the type it asked for: a .py
        # for a script, a .csv for data, .sql for a query. Released on the same
        # terms as any other deliverable - only once a person has approved it.
        if task_type != "chat" and approval in ("approved", "not required"):
            for name, body in _artifacts(deliverable, _document_title(prompt)):
                written = await self._use_tool(
                    __tools__, "save_artifact", filename=name, content=body
                )
                if written and not written.startswith(_ERR):
                    if "save_artifact" not in tools_used:
                        tools_used.append("save_artifact")
                    trace.append(f"**TOOL** `save_artifact` wrote `{name}`.")
                    deliverable += "\n\n" + written

        # PS 26117 asks for the approval note as a Word file. Produce it only once a
        # person has released the result, never before.
        if task_type in ("document", "vision") and approval in ("approved", "not required"):
            await _status(__event_emitter__, "tool", "TOOL: writing the Word deliverable")
            docx = await self._use_tool(
                __tools__,
                "create_word_document",
                title=_document_title(prompt),
                body=deliverable,
                reference="Produced by the 4CE agent chain; "
                + (", ".join(tools_used) if tools_used else "no tools attached"),
                __user__=__user__,
            )
            if docx and not docx.startswith(_ERR):
                tools_used.append("create_word_document")
                trace.append(
                    "**TOOL** `create_word_document` wrote the released result to a .docx."
                )
                deliverable += "\n\n---\n\n" + docx

        await _status(__event_emitter__, "done", "Complete", done=True)

        if not self.valves.show_reasoning:
            return deliverable
        return deliverable + "\n\n" + _provenance(
            steps, task_type, signals, model_id, rationale, verdict, approval,
            time.monotonic() - started - waited, attempts, self.valves.show_model_thinking,
            trace if self.valves.show_trace else [], agent_models, tools_used, grounding,
        )

    async def _model_collections(self, metadata: dict) -> list[str]:
        """Knowledge bases attached to this model, read from the model itself.

        The platform only folds a model's knowledge into the request when that
        model is set to legacy function calling; a pipe is not, so `files`
        arrives empty and the chain retrieves nothing while the workspace shows
        a knowledge base confidently attached. Nothing errors - the answer just
        quietly stops being grounded, which is the one failure this chain is
        supposed to make visible. Reading the attachment from the model record
        removes the dependency on a flag that has no bearing on retrieval.
        """
        model_id = (metadata or {}).get("model") or ""
        if isinstance(model_id, dict):
            model_id = model_id.get("id") or ""
        if not model_id:
            return []
        try:
            from open_webui.models.models import Models

            record = await Models.get_model_by_id(model_id)
        except Exception:
            return []
        if record is None:
            return []

        meta = getattr(record, "meta", None)
        attached = getattr(meta, "knowledge", None) if meta is not None else None
        if attached is None and isinstance(meta, dict):
            attached = meta.get("knowledge")

        collections: list[str] = []
        for item in attached or []:
            if not isinstance(item, dict):
                continue
            names = item.get("collection_names") or []
            if names:
                collections += [n for n in names if n]
                continue
            single = item.get("collection_name") or item.get("id")
            if single:
                collections.append(single)
        return collections

    async def _retrieve(self, request: Any, user: Any, metadata: dict, query: str) -> str:
        """Passages from any knowledge base attached to this request.

        Retrieval is done here rather than taken from the platform. The platform
        grounds an ordinary model by rewriting the system message, but every agent
        in this chain is given a system prompt of its own, so that context never
        survives to the agent that needs it. The failure is quiet: the answer
        looks grounded and is not.
        """
        collections: list[str] = []
        for item in (metadata or {}).get("files") or []:
            if not isinstance(item, dict):
                continue
            names = (item.get("data") or {}).get("collection_names") or []
            collections += [n for n in names if n]
            if not names:
                single = item.get("collection_name") or (
                    item.get("id") if item.get("type") == "collection" else None
                )
                if single:
                    collections.append(single)
        if not collections:
            collections = await self._model_collections(metadata)
        collections = list(dict.fromkeys(collections))
        if not collections:
            return ""

        try:
            from open_webui.retrieval.utils import query_collection

            found = await query_collection(
                request,
                collection_names=collections,
                queries=[query],
                embedding_function=lambda q, prefix: request.app.state.EMBEDDING_FUNCTION(
                    q, prefix=prefix, user=user
                ),
                k=self.valves.retrieval_k,
            )
        except Exception:
            return ""

        passages = [
            text
            for group in ((found or {}).get("documents") or [])
            for text in (group or [])
            if text and text.strip()
        ]
        return "\n\n---\n\n".join(passages[: self.valves.retrieval_k])

    async def _use_tool(self, tools: dict | None, name: str, **kwargs: Any) -> str:
        """Call one deployed 4CE tool by its function name.

        Returns "" when the tool is not attached to this model, so the chain
        degrades to unaided reasoning instead of failing. The provenance records
        which tools ran, so an absent tool is visible rather than silent.
        """
        entry = (tools or {}).get(name) or {}
        fn = entry.get("callable")
        if not callable(fn):
            return ""
        try:
            result = fn(**kwargs)
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:
            return f"{_ERR} {name} failed: {exc}"
        return str(result or "").strip()

    def _agent_model(
        self,
        override: str,
        routed: str,
        available: list[str],
        independent: bool = False,
    ) -> str:
        """An agent's assigned model, falling back to the routed one."""
        wanted = (override or "").strip()
        if wanted:
            return _match_model(wanted, available, "") or routed
        if independent and self.valves.independent_verification:
            return self._alternate_model(routed, available) or routed
        return routed

    def _alternate_model(self, routed: str, available: list[str]) -> str | None:
        """Any served model that is not the routed one.

        ULTRON grading JARVIS on the same weights reproduces the same blind spot,
        so a blank ULTRON override crosses to a different model rather than
        quietly agreeing with itself.
        """
        for wanted in (
            self.valves.analysis_model,
            self.valves.coding_model,
            self.valves.chat_model,
            self.valves.vision_model,
        ):
            candidate = _match_model((wanted or "").strip(), available, "")
            if candidate and candidate != routed:
                return candidate
        return next((c for c in available if c != routed), None)

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
        usage = _usage_of(response)
        raw, separate_reasoning = _response_parts(response)
        if not raw.strip() and not separate_reasoning.strip():
            return _step(f"{_ERR} local model '{model}' returned an empty response.", "", model, started, usage)
        answer, inline_thinking = _split_thinking(raw.strip())
        thinking = "\n\n".join(t for t in (separate_reasoning.strip(), inline_thinking) if t)
        return _step(answer or raw.strip(), thinking, model, started, usage)


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
    "any action.\n\n"
    "Answer only what was asked. A greeting gets a greeting back and nothing else: "
    "reply to 'hello' with something like 'Hello. What can I help you with?' and stop "
    "there. Describe the agents ONLY when the question is explicitly about what you "
    "are or what you can do. Listing them in response to a greeting is wrong.\n\n"
    "When you do name them, the names are exactly TONY, FRIDAY, JARVIS and ULTRON. "
    "Copy those spellings character for character; do not reconstruct them from "
    "memory, because an invented name is the first thing a reader notices."
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


_READING_UNITS = (
    r"drops?\s*(?:per\s*minute|/\s*min|pm)", r"mm\s*/\s*s", r"mm", r"microns?", r"µm", r"um",
    r"bar(?:\s*g)?", r"kpa", r"mpa", r"psi", r"°\s*c", r"deg\s*c", r"\bc\b", r"rpm", r"hz",
    r"%", r"litres?\s*/\s*min", r"l\s*/\s*min", r"m3\s*/\s*h",
)
_READING_PATTERN = re.compile(
    r"\d+(?:\.\d+)?\s*(?:" + "|".join(_READING_UNITS) + r")\b", re.I
)


def _has_readings(text: str) -> bool:
    """Whether there is anything for the threshold rule pack to assess.

    The check is deterministic and cheap, but running it on a request that
    carries no measurements puts a row in the provenance table claiming an SOP
    comparison happened - on, say, a sovereignty audit, where there is nothing
    to compare. A reviewer reading that table should see the tools that acted
    on this request and no others.
    """
    return bool(_READING_PATTERN.search(text or ""))


def _wants_audit(prompt: str) -> bool:
    """Whether the request is asking for the sovereignty claim to be evidenced."""
    lowered = prompt.lower()
    return any(signal in lowered for signal in AUDIT_SIGNALS)


def _extract_python(text: str) -> str:
    """Every fenced Python block in a deliverable, joined in order.

    Taking only the first block silently defeats the sandbox: a model typically
    puts the definition in one block and the call that demonstrates it in the
    next, so running the first alone defines a function and exits with no
    output - which then reads as a result that proves nothing, and ULTRON fails
    it. Interpreter transcripts and shell lines are skipped; they are
    illustration, not a program.
    """
    blocks = re.findall("```(?:python|py)\s*\n(.*?)```", text, re.S | re.I)
    usable = [
        block.strip()
        for block in blocks
        if block.strip() and not block.lstrip().startswith((">>>", "$ "))
    ]
    if usable:
        return "\n\n".join(usable)
    return _unfenced_python(text)


def _unfenced_python(text: str) -> str:
    """Code a model wrote and forgot to fence.

    Small models are inconsistent about code fences, and an unfenced answer left
    the sandbox with nothing to run and produced no .py - the request looked
    answered while nothing had been executed. The parser decides: the longest
    run of leading lines Python accepts, provided it is a program rather than a
    stray word, is the code.
    """
    program = (
        ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign,
        ast.AugAssign, ast.AnnAssign, ast.Import, ast.ImportFrom, ast.For,
        ast.While, ast.If, ast.With, ast.Try,
    )
    lines = text.splitlines()
    for end in range(len(lines), 0, -1):
        candidate = "\n".join(lines[:end]).strip()
        if not candidate:
            continue
        try:
            tree = ast.parse(candidate)
        except (SyntaxError, ValueError):
            continue
        looks_like_code = any(
            isinstance(node, program)
            or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call))
            for node in tree.body
        )
        if looks_like_code:
            return candidate
    return ""


_LANGUAGE_SUFFIX = {
    "python": "py", "py": "py", "sql": "sql", "javascript": "js", "js": "js",
    "typescript": "ts", "ts": "ts", "java": "java", "c": "c", "cpp": "cpp",
    "c++": "cpp", "csharp": "cs", "cs": "cs", "go": "go", "golang": "go",
    "rust": "rs", "rs": "rs", "ruby": "rb", "rb": "rb", "bash": "sh",
    "sh": "sh", "shell": "sh", "powershell": "ps1", "ps1": "ps1", "r": "r",
    "matlab": "m", "csv": "csv", "tsv": "tsv", "json": "json", "yaml": "yaml",
    "yml": "yaml", "xml": "xml", "html": "html", "css": "css",
    "markdown": "md", "md": "md", "ini": "ini", "toml": "toml",
    "text": "txt", "txt": "txt", "plaintext": "txt",
}


def _artifacts(text: str, title: str) -> list[tuple[str, str]]:
    """The files a deliverable is asking to become, named and typed.

    A model asked for a script writes the definition in one fenced block and the
    call in the next, so blocks of the same language are joined into one file
    rather than scattered across several. Relying on the model to save its own
    files does not work - told to write to a specific directory it will write to
    one it invented instead - so the artefact is taken from what it actually
    produced.
    """
    grouped: dict[str, list[str]] = {}
    for language, block in re.findall("```(\w*)[^\S\n]*\n(.*?)```", text, re.S):
        suffix = _LANGUAGE_SUFFIX.get(language.strip().lower())
        body = block.strip()
        if suffix and body:
            grouped.setdefault(suffix, []).append(body)

    if not grouped:
        # Same reason the sandbox needs it: an unfenced answer is still code, and
        # without this it would be shown and never saved.
        loose = _unfenced_python(text)
        if loose:
            grouped["py"] = [loose]

    files = []
    for suffix, parts in grouped.items():
        body = "\n\n".join(parts)
        files.append((f"{_artifact_stem(title, body, suffix)}.{suffix}", body))
    return files


def _artifact_stem(title: str, body: str, suffix: str) -> str:
    """A short, recognisable filename for a produced artefact.

    Naming the file after the whole request produces
    `write_a_python_function_that_returns_the_median_of.py`, which is the
    request rather than the thing, and unreadable in a download list. Code
    names itself: the first definition in the file is what the reader is
    looking for. Anything else falls back to the subject of the request with
    the instruction to produce it removed.
    """
    if suffix == "py":
        try:
            for node in ast.parse(body).body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    return node.name.lower()
        except SyntaxError:
            pass
    words = _subject_words(title)
    stem = "_".join(words[:5]).lower()
    return re.sub("[^a-z0-9_]+", "", stem).strip("_") or "artifact"


# Openers that state what to do rather than what the result is about.
_REQUEST_OPENERS = (
    "write", "draft", "create", "produce", "generate", "make", "build", "give",
    "show", "provide", "prepare", "compose", "summarise", "summarize", "list",
    "me", "a", "an", "the", "some", "please", "us", "code", "for",
)


def _subject_words(title: str) -> list[str]:
    """The words of a request that describe its subject, not its instruction."""
    words = re.findall("[A-Za-z0-9-]+", title or "")
    while words and words[0].lower() in _REQUEST_OPENERS:
        words.pop(0)
    return words or ["artifact"]


def _document_title(prompt: str) -> str:
    """A short title describing the deliverable, not the request for it.

    The whole prompt used to become both the heading and the filename, which
    gave documents called `What_is_the_acceptable_mechanical_seal_leakage_rate
    _under_SO.docx` - truncated mid-word, and phrased as a question the
    document answers rather than as its subject.
    """
    cleaned = re.sub("\s+", " ", prompt or "").strip()
    if not cleaned:
        return "4CE deliverable"
    # A request often states its subject after a colon; prefer what precedes it.
    head = cleaned.split(":", 1)[0]
    words = _subject_words(head)[:8]
    title = " ".join(words).rstrip(" ,.;:?")
    return (title[:1].upper() + title[1:]) if title else "4CE deliverable"


def _available_models(request: Any) -> list[str]:
    try:
        models = request.app.state.MODELS
        keys = list(models.keys()) if hasattr(models, "keys") else []
    except Exception:
        return []
    # The orchestrator registers itself as a model. Its id is "ace_orchestrator.*",
    # which the "4ce" test does not catch, and routing an agent to it would recurse.
    return [
        k
        for k in keys
        if "4ce" not in k.lower() and not k.lower().startswith("ace_orchestrator")
    ]


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


def _retrieved_context(messages: list[dict]) -> str:
    """Whatever retrieval put in front of the chain.

    The platform injects knowledge-base passages by rewriting the system
    message. Each agent is then given its own system prompt, so unless that
    injected text is carried across explicitly it is dropped on the floor and
    the agents answer from the model's own memory while appearing to be
    grounded - the worst of both, because nothing looks wrong.
    """
    parts = [
        _text_of(m).strip()
        for m in messages
        if isinstance(m, dict) and m.get("role") == "system"
    ]
    return "\n\n".join(p for p in parts if p)


def _grounding_text(messages: list[dict]) -> str:
    """Only the passages retrieval actually put in front of the chain.

    `_retrieved_context` returns every system message, because all of it has to
    be carried across to the agents. That is the right input for the prompt and
    the wrong number for the provenance table: a request with no knowledge base
    still arrives with an ambient platform preamble, so counting system
    characters reports grounding on every turn, including turns where nothing
    was retrieved - the provenance row then asserts exactly the thing it exists
    to disprove.

    The platform wraps injected passages in the RAG template's `<context>`
    block, so that block is the honest measure. No block means no retrieval.
    """
    found: list[str] = []
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "system":
            continue
        text = _text_of(message)
        for chunk in re.findall(r"<context>(.*?)</context>", text, re.DOTALL):
            chunk = chunk.strip()
            if chunk:
                found.append(chunk)
    return "\n\n".join(found)


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


def _step(text: str, thinking: str, model: str, started: float,
          usage: dict | None = None) -> dict:
    return {
        "text": text,
        "thinking": thinking,
        "model": model,
        "seconds": time.monotonic() - started,
        "usage": usage or {},
    }


def _usage_of(response: Any) -> dict:
    """The token counts the local model server reported for one agent call."""
    payload = response
    if isinstance(payload, list) and len(payload) == 1:
        payload = payload[0]
    if not isinstance(payload, dict):
        return {}
    usage = payload.get("usage")
    return usage if isinstance(usage, dict) else {}


def _usage_total(steps: list[dict]) -> dict:
    """Add up a run's agent calls so the turn reports what it actually cost.

    A pipe owns the whole turn, so the platform never sees the individual
    completions and records nothing: every chat shows zero tokens, and the
    usage and analytics pages report a system that apparently does no work.
    The chain knows the real numbers - it just has to hand them back.
    """
    prompt = completion = 0
    for step in steps:
        usage = step.get("usage") or {}
        prompt += int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        completion += int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    if not (prompt or completion):
        return {}
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
    }


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
                agent_models: dict, tools_used: list[str] | None = None,
                grounding: str = "") -> str:
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
        # Working time, not wall clock: the reviewer's reading time belongs to
        # the reviewer, and counting it makes a fast run look like a slow one.
        ("Elapsed", f"{elapsed:.0f}s working" + (f" · {timings}" if timings else "")),
        (
            "Grounding",
            f"{len(grounding):,} characters of retrieved passages reached FRIDAY"
            if grounding
            else "none — nothing retrieved, answered from the request alone",
        ),
        (
            "Tools run",
            " · ".join(f"`{t}`" for t in tools_used)
            if tools_used
            else "none — the agents reasoned unaided",
        ),
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


