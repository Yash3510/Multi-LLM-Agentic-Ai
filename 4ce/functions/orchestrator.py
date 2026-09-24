"""
title: 4CE Orchestrator
author: 4CE
version: 0.1.0
description: Sovereign multi-agent orchestrator. TONY classifies and routes, FRIDAY grounds, JARVIS executes, ULTRON verifies, a human approves. All inference stays on locally served open-weight models.
"""

import ast
import asyncio
import difflib
import hashlib
import inspect
import json
import re
import time
from datetime import datetime
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
    # How people actually ask - including the starter prompt install.py puts
    # on the empty chat, which matched none of the above and was answered as
    # a document task about pump SOPs.
    "off-premise", "off premise", "off the premises", "send data", "sends data",
    "sending data", "data leave", "anything leave", "egress", "outbound connection",
    "network monitor", "audit this deployment", "audit the deployment",
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
        # What the workbench's processes connect to from here to the answer
        # is observed, not assumed: the receipt reports it (_egress_since).
        egress_mark = _egress_mark()
        messages = body.get("messages") or []
        if not messages:
            return "No request received."

        # Open TONY's stage the moment work starts. Classification and the
        # retrieval that follows it both run before TONY's plan is announced,
        # so without this the chat's stage rail could only measure the gap
        # after them and showed TONY as "<0.1s".
        await _status(__event_emitter__, "tony", "TONY: reading the request")

        prompt = _text_of(messages[-1])
        has_image = _has_image(messages[-1])
        retrieved = _retrieved_context(messages)
        grounding = _grounding_text(messages)

        user = await Users.get_user_by_id(__user__["id"])
        if user is None:
            return "4CE could not resolve the requesting user."

        task_type, signals = _classify(prompt, has_image)
        # A sovereignty question is about this deployment, not the plant. The
        # audit answers it; pump procedures retrieved beside it only give
        # FRIDAY something irrelevant to reason about.
        auditing = _wants_audit(prompt)

        # Retrieve after classifying, and only where documents can help. An
        # attached knowledge base is queried on every turn otherwise, so a
        # greeting or a request for a median function arrives carrying several
        # thousand characters of pump procedures: slower on a small card, and
        # provenance that claims a median was grounded in plant SOPs.
        sources: list[dict] = []
        if task_type in RETRIEVING_TASKS and not auditing:
            found = await self._retrieve(__request__, user, __metadata__, prompt)
            if found:
                sources, numbered = _number_sources(found)
                retrieved = f"{retrieved}\n\n{numbered}".strip() if retrieved else numbered
                grounding = f"{grounding}\n\n{numbered}".strip() if grounding else numbered
                # The chat shows these under the answer, and turns each [n] in
                # the answer into a chip that opens the passage it stands on.
                for source in sources:
                    await _emit_source(__event_emitter__, source)

        await _status(
            __event_emitter__,
            "tony_plan",
            f"TONY: classified as {task_type.upper()}"
            + (f" ({', '.join(signals)})" if signals else " (no strong signal, defaulting)"),
            facts=[
                f"Classified as a {task_type} task",
                f"Matched on: {', '.join(signals)}" if signals else "No strong signal, so the default route",
                f"{len(grounding):,} characters retrieved to work from" if grounding else "",
            ],
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
        await _status(
            __event_emitter__, "router", f"ROUTER: selected {model_id} — {rationale}",
            facts=[f"Routed to {model_id}", rationale[:1].upper() + rationale[1:] if rationale else ""],
        )
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
            # Open while the model answers, closed once it has: marking it done up
            # front left the status reading "Answering directly" on a finished
            # reply, and meant nothing showed the model was working meanwhile.
            await _status(__event_emitter__, "chat", "Answering directly")
            reply = await self._agent_call(
                __request__, user, model_id, messages,
                system=_TONY_CHAT_SYSTEM, instruction=prompt,
            )
            if reply["text"].startswith(_ERR):
                await _status(__event_emitter__, "error", "Run failed", done=True)
                return reply["text"]
            await _status(__event_emitter__, "chat", "Answered directly", done=True)
            # Recorded even though this path shows no provenance table: it is
            # still a model call, and the turn's token accounting reads steps.
            steps.append({**reply, "agent": "TONY", "label": "direct reply"})
            # Plain markdown, not HTML: the renderer special-cases only a handful
            # of tags and prints every other one as literal text.
            note = (
                f"\n\n*Direct reply \u00b7 `{model_id}` \u00b7 {reply['seconds']:.1f}s \u2014 "
                "conversation needs no agent chain or approval*"
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
        # The draft ULTRON sent back and why, kept to show what try 2 changed.
        first_try: dict | None = None
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
        if auditing:
            await _status(
                __event_emitter__, "tool", "TOOL: auditing the configuration and the observed egress"
            )
            audit = await self._use_tool(__tools__, "verify_sovereignty")
            if audit and not audit.startswith(_ERR):
                tools_used.append("verify_sovereignty")
                steps.append({
                    "agent": "TOOL",
                    "label": "sovereignty audit",
                    "model": "configuration read and egress observation",
                    "seconds": 0.0,
                    "thinking": "",
                    "text": audit,
                })
                trace.append(
                    "**TOOL** `verify_sovereignty` read the live configuration and "
                    "what the workbench was observed connecting to."
                )
            else:
                audit = ""

        while True:
            attempts += 1

            round_label = "" if attempts == 1 else f" (attempt {attempts})"

            await _status(
                __event_emitter__, "friday", "FRIDAY: grounding and analysing",
                facts=[
                    f"Reading {len(grounding):,} characters of retrieved passages"
                    if grounding else "No retrieved passages; working from the request alone",
                    f"Running on {agent_models['FRIDAY']}",
                    "Second try, with ULTRON's objections attached" if attempts > 1 else "",
                ],
            )
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
                    + (_CITE_RULE.format(numbers=_source_numbers(sources)) if sources else "")
                    + "\n\nREQUEST\n"
                    + prompt,
                    challenge,
                ),
                pass_images=has_image,
            )
            analysis = friday["text"]
            if analysis.startswith(_ERR):
                await _status(__event_emitter__, "error", "Run failed", done=True)
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

            await _status(
                __event_emitter__, "jarvis", "JARVIS: producing the deliverable",
                facts=[
                    f"Running on {agent_models['JARVIS']}",
                    "Working from FRIDAY's analysis",
                    "Its code will run in the sealed sandbox" if task_type == "code" else "",
                    "Second try, with ULTRON's objections attached" if attempts > 1 else "",
                ],
            )
            jarvis = await self._agent_call(
                __request__, user, agent_models["JARVIS"], messages,
                system=_JARVIS_SYSTEM,
                instruction=(
                    f"ORIGINAL REQUEST\n{prompt}\n\n"
                    f"FRIDAY'S ANALYSIS\n{analysis}"
                    + grounded
                    + (
                        "\n\nSOURCES\n"
                        + "\n".join(f"[{n}] {src['name']}" for n, src in enumerate(sources, 1))
                        + "\n\nKeep FRIDAY's bracketed source numbers on every claim you carry "
                        "over, placed straight after the claim, exactly as written - for "
                        "example \"The leakage limit is 5 drops per minute [1].\" Never add "
                        f"a number that is not in the list above ({_source_numbers(sources)}), "
                        "and never present an unnumbered claim as coming from the documents."
                        if sources
                        else ""
                    )
                    + (
                        "\n\nPut every line of code inside a fenced ```python block. "
                        "This code will be executed. If the request calls for a file - "
                        "a spreadsheet, a chart, an export - write it into the directory "
                        "/output, which is returned to the user. Nowhere else is writable. "
                        "End the program by checking its own result: assert what the "
                        "request's example should produce, then print it. A failed assert "
                        "fails the run and sends the code back to be fixed."
                        if task_type == "code"
                        else ""
                    )
                    + (
                        "\n\nPREVIOUS ATTEMPT WAS REJECTED FOR:\n" + challenge
                        if challenge and task_type == "code"
                        else ""
                    )
                    + "\n\nProduce the finished deliverable the request actually asked "
                    "for. Show working for any calculation. Do not claim you performed an "
                    "action unless it is supported by the analysis above. Where a section "
                    "above is marked authoritative, quote its verdicts as they stand and "
                    "do not recompute them."
                    + _ANSWER_SHAPE
                ),
            )
            deliverable = _check_citations(jarvis["text"], len(sources))
            if deliverable.startswith(_ERR):
                await _status(__event_emitter__, "error", "Run failed", done=True)
                return deliverable
            # Tidied before ULTRON reads it, so the text it checks is the text
            # that is released, fingerprinted and written into the report.
            deliverable = _tidy(deliverable)
            steps.append({**jarvis, "agent": "JARVIS", "label": f"deliverable{round_label}"})
            trace.append(f"**JARVIS** produced the deliverable in {jarvis['seconds']:.1f}s.")

            # Generated code is run, not admired. The real output is appended so
            # ULTRON and the reviewer judge what actually executed.
            ran = None
            if task_type == "code":
                code = _extract_python(deliverable)
                execution = ""
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
                        deliverable += "\n\n### Sandboxed execution result\n\n" + execution
                # What the sandbox reported, as 4CE's own check - not left for a
                # 1.7B verifier to notice that the program crashed.
                ran = _execution_check(code, execution, prompt)

            if not self.valves.enable_verification:
                verdict = {"status": "SKIPPED", "passed": True, "detail": "Verification disabled in Valves."}
                break

            await _status(
                __event_emitter__, "ultron", "ULTRON: challenging the result",
                facts=[
                    f"Checking on {agent_models['ULTRON']}"
                    + (", not the model that drafted it" if agent_models["ULTRON"] != agent_models["JARVIS"] else ""),
                    "Its verdict is PASS or FAIL, with reasons",
                ],
            )
            ultron = await self._agent_call(
                __request__, user, agent_models["ULTRON"], messages,
                system=_ULTRON_SYSTEM,
                think=False,
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
                    "Reply with PASS or FAIL on the first line. Then go through the result's "
                    "claims in order and give each claim exactly one line - never two lines "
                    "about the same claim. Start the line with OK: when the claim holds, "
                    "PROBLEM: when the result contradicts itself, gets arithmetic wrong, or "
                    "states something neither the request nor the result gives any basis for, "
                    "or UNVERIFIED: when nothing supplied settles it. A difference of wording "
                    "(\"below\" and \"less than\") is not a problem. After the label, name the "
                    "claim in a few words and say why. PROBLEM lines are your reasons for a FAIL."
                ),
            )
            verdict = _parse_verdict(ultron["text"])
            # The card under the answer: what 4CE confirmed mechanically, then
            # ULTRON's own checks.
            verdict["checks"] = (
                ([ran] if ran else [])
                + _figure_checks(deliverable, sources)
                + _parse_checks(verdict["detail"])
            )
            verdict["cited_text"] = deliverable
            # A figure cited to a document that does not contain it is wrong
            # whatever ULTRON concluded: the answer fails and goes round again.
            mismatched = [c["text"] for c in verdict["checks"] if c.get("by") == "4CE" and c["kind"] == "problem"]
            if mismatched and verdict["passed"]:
                verdict.update(
                    status="FAIL",
                    passed=False,
                    failed_by="4CE",
                    failed_on="execution" if ran and ran["kind"] == "problem" else "figure",
                    summary=_clip(mismatched[0]),
                    detail="\n".join(f"PROBLEM: {m}" for m in mismatched) + "\n" + verdict["detail"],
                )
            # Code nobody ran has not been verified, whatever ULTRON read into
            # it. A second try cannot start a sandbox, so this one is final.
            if ran and ran.get("final") and verdict["passed"]:
                verdict.update(
                    status="FAIL",
                    passed=False,
                    failed_by="4CE",
                    failed_on="not executed",
                    summary=_clip(ran["text"]),
                    detail=f"UNVERIFIED: {ran['text']}\n" + verdict["detail"],
                )
            # A PASS with objections listed beneath it is two answers at once.
            # The verdict word decides - on the runs seen here the 1.7B
            # verifier's word was right and its line-by-line objections were
            # not - but the record says both, so nobody is shown a clean tick
            # over "a problem".
            if verdict["passed"]:
                verdict["reservations"] = sum(
                    1 for c in verdict["checks"] if c.get("by") == "ULTRON" and c["kind"] != "ok"
                )
            steps.append({
                **ultron,
                "agent": "ULTRON",
                "label": f"verification{round_label} — {verdict['status']}",
            })
            trace.append(f"**ULTRON** returned `{verdict['status']}` in {ultron['seconds']:.1f}s.")

            if verdict["passed"]:
                await _status(
                __event_emitter__, "ultron",
                "ULTRON: PASS" + _reservations_phrase(verdict, ", with "),
            )
                break

            await _status(
                __event_emitter__, "ultron",
                "ULTRON: FAIL" + (f" — {verdict['summary']}" if verdict.get("summary") else ""),
            )
            if not self.valves.enable_replan or attempts > 1 or (ran and ran.get("final")):
                trace.append("**TONY** exhausted the replan budget; delivering with the failure recorded.")
                break

            # FRIDAY hears the objections, not the checks that passed.
            objections = [c["text"] for c in _parse_checks(verdict["detail"]) if c["kind"] != "ok"]
            checks = verdict.get("checks") or []
            first_try = {
                "draft": deliverable,
                "failed_by": verdict.get("failed_by") or "ULTRON",
                # What it objected to: its problems, else what it could not
                # verify, else the verdict's own summary.
                "objections": [(c["text"], c.get("by", "ULTRON")) for c in checks if c["kind"] == "problem"]
                or [(c["text"], c.get("by", "ULTRON")) for c in checks if c["kind"] == "unverified"]
                or [(_clip(verdict.get("summary") or verdict.get("detail", ""), 220), "ULTRON")],
            }
            challenge = "\n".join(f"- {o}" for o in objections) if objections else verdict["detail"]
            await _status(
                __event_emitter__, "tony_replan", "TONY: replanning after ULTRON challenge",
                facts=["FRIDAY and JARVIS run again with ULTRON's objections attached"],
            )
            trace.append("**TONY** replanned once and re-ran FRIDAY and JARVIS with the challenge attached.")

        if first_try and verdict:
            verdict["revision"] = _revision(first_try, deliverable, verdict)

        approval = "not required"
        approved_at: datetime | None = None
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
            await _status(
                __event_emitter__, "approval", "Awaiting human approval",
                facts=[f"ULTRON's verdict: {str(verdict.get('status', 'UNKNOWN')).upper()}"],
            )
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
                        "title": "Review before release",
                        "message": _approval_message(deliverable, verdict, task_type, model_id),
                        # Not the word itself: a grey "APPROVE" in an empty box reads
                        # as already filled in, so people pressed Confirm on nothing
                        # and were told the result was withheld.
                        "placeholder": "Type approve to release",
                        # Structured copy of the same decision for the 4CE sign-off
                        # panel, which docks in place of the message box instead of
                        # covering the conversation with a modal. `message` above is
                        # kept, so a frontend without the panel still gets the dialog.
                        # The decision is still made here, below: anything but
                        # "approve" withholds.
                        "kind": "4ce_approval",
                        "draft": (deliverable or "").strip(),
                        "verdict": str(verdict.get("status", "UNKNOWN")).upper(),
                        "reservations": verdict.get("reservations", 0),
                        "verdict_detail": _objection(verdict),
                        "task_type": task_type,
                        "model_id": model_id,
                        # The checks, the passages behind each [n] and what a
                        # second try changed, so the reviewer decides on the
                        # same record the answer and the report carry.
                        **_review(deliverable, verdict, sources, attempts),
                    },
                }
            )
            waited = time.monotonic() - asked_at
            # No answer is not a "no". When the prompt cannot reach the reviewer's
            # browser (the tab reloaded or closed) or nobody answers before the
            # timeout, the platform returns {"error": ...} - measured: a page
            # reload during a run came back in under 0.1s and was recorded as
            # "Rejected by reviewer", putting a decision nobody made into the
            # audit trail. The result is withheld either way; only the record
            # differs, and the record is the point.
            if isinstance(response, dict) and response.get("error"):
                approval = "not obtained — no reviewer answered"
                trace.append(
                    f"**HUMAN** approval was not obtained ({response.get('error')}); "
                    "the result was not released."
                )
                await _status(__event_emitter__, "approval", "No reviewer answered", done=True)
                return (
                    "### Deliverable withheld\n\n"
                    "No reviewer answered the sign-off, so 4CE has not released this result. "
                    "Nothing was approved or rejected; ask again to review it.\n\n"
                    + _provenance(
                        steps, task_type, signals, model_id, rationale, verdict, approval,
                        time.monotonic() - started - waited, attempts, self.valves.show_model_thinking,
                        trace if self.valves.show_trace else [], agent_models, tools_used, grounding,
                        sources=sources, egress=_egress_since(egress_mark),
                    )
                )
            decision = response if isinstance(response, str) else ""
            approved = decision.strip().lower() in ("approve", "approved")
            if approved:
                approval = "approved"
                approved_at = datetime.now().astimezone()
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
                        sources=sources, egress=_egress_since(egress_mark),
                    )
                )

        # The released answer's fingerprint: SHA-256 of its exact text, taken
        # before any file links are added. The receipt, the provenance and the
        # Word report all carry it, so a copy can be checked against the
        # record - one changed character gives a different fingerprint.
        verdict["cited_text"] = deliverable
        fingerprint = (
            hashlib.sha256(deliverable.strip().encode("utf-8")).hexdigest()
            if approval in ("approved", "not required")
            else ""
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
            await _status(
                __event_emitter__, "tool", "TOOL: writing the Word deliverable",
                facts=["Writing a .docx of the approved result"],
            )
            # The report carries the same record the chat shows, and who
            # approved it and when. Passed as "__" parameters, which the tool
            # spec hides from models: only this code ran the approval gate,
            # so only it may say that a person approved the document.
            record = [
                (label, re.sub(r"[`*]", "", value))
                for label, value in _provenance_rows(
                    task_type, signals, model_id, rationale, verdict, approval,
                    time.monotonic() - started - waited, attempts, agent_models, tools_used, grounding,
                    egress=_egress_since(egress_mark),
                )
            ]
            if fingerprint:
                record.append(("Fingerprint", f"SHA-256 {fingerprint} of the released answer"))
            signoff = {
                "fingerprint": fingerprint,
                "verification": str(verdict.get("status", "n/a")).upper()
                + (f" after {attempts} attempts" if attempts > 1 else "")
                + _reservations_phrase(verdict, ", with "),
                "models": " · ".join(dict.fromkeys(m.rsplit("/", 1)[-1] for m in agent_models.values())),
            }
            if approval == "approved" and approved_at is not None:
                approver = (getattr(user, "name", "") or getattr(user, "email", "") or "").strip() or "the reviewer"
                when = f"{approved_at.day} {approved_at:%B %Y}, {approved_at:%H:%M} {approved_at.tzname() or ''}".strip()
                signoff.update(approved_by=approver, approved_at=when)
                record = [
                    (label, f"Approved by {approver} on {when}" if label == "Human approval" else value)
                    for label, value in record
                ]
            docx = await self._use_tool(
                __tools__,
                "create_word_document",
                title=_document_title(prompt),
                body=deliverable,
                document_type="Approved deliverable" if approval == "approved" else "Deliverable",
                __user__=__user__,
                __signoff__=signoff,
                __record__=record,
                # The documents the [n] in the text refer to, listed at the end.
                __sources__=[source["name"] for source in sources],
                # What a replan changed, when ULTRON sent the first draft back.
                __revision__=verdict.get("revision"),
                # The checks made before release, and what each cited [n]
                # rests on: the passage retrieved from that document.
                __checks__=verdict.get("checks") or [],
                __passages__=[
                    _supporting_text(
                        "\n".join(p["text"] for p in source["passages"]),
                        _cited_figures(deliverable, len(sources)).get(n, set()),
                    )
                    for n, source in enumerate(sources, 1)
                ],
                __cited__=_cited_numbers(deliverable, len(sources)),
            )
            if docx and not docx.startswith(_ERR):
                tools_used.append("create_word_document")
                trace.append(
                    "**TOOL** `create_word_document` wrote the released result to a .docx."
                )
                deliverable += "\n\n" + _file_card(docx)

        await _status(__event_emitter__, "done", "Complete", done=True)

        if not self.valves.show_reasoning:
            return deliverable
        approver = when = ""
        if approval == "approved" and approved_at is not None:
            approver = (getattr(user, "name", "") or getattr(user, "email", "") or "").strip()
            when = f"{approved_at:%H:%M}"
        return deliverable + "\n\n" + _provenance(
            steps, task_type, signals, model_id, rationale, verdict, approval,
            time.monotonic() - started - waited, attempts, self.valves.show_model_thinking,
            trace if self.valves.show_trace else [], agent_models, tools_used, grounding,
            sources=sources, approver=approver, approved_at=when, fingerprint=fingerprint,
            egress=_egress_since(egress_mark),
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

    async def _retrieve(self, request: Any, user: Any, metadata: dict, query: str) -> list[dict]:
        """Passages from any knowledge base attached to this request, each with
        the file it came from, so the answer can cite it.

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
            return []

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
            return []

        found = found or {}
        documents = found.get("documents") or []
        metadatas = found.get("metadatas") or []
        distances = found.get("distances") or []
        passages: list[dict] = []
        for g, group in enumerate(documents):
            for i, text in enumerate(group or []):
                if not text or not text.strip():
                    continue
                meta = dict(((metadatas[g] if g < len(metadatas) else None) or [None] * (i + 1))[i] or {})
                distance = ((distances[g] if g < len(distances) else None) or [None] * (i + 1))[i]
                passages.append({
                    "text": text.strip(),
                    "name": str(meta.get("name") or meta.get("source") or "Knowledge base"),
                    "meta": meta,
                    "distance": distance,
                })
        return passages[: self.valves.retrieval_k]

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
        system: str, instruction: str, pass_images: bool = False, think: bool = True,
    ) -> str:
        if not think:
            # Qwen3's switch for answering without a reasoning pass. ULTRON's
            # 1.7B model otherwise spent most of its reply budget thinking out
            # loud and was cut off mid-line, or never reached its verdict.
            instruction += "\n\n/no_think"
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
            return _step(
                _failure(f"local model call to '{model}' failed", _explain(exc)),
                "", model, started,
            )
        usage = _usage_of(response)
        raw, separate_reasoning = _response_parts(response)
        if not raw.strip() and not separate_reasoning.strip():
            # An upstream refusal arrives here as a reply with no content, so
            # reporting "empty response" sends the reader to restart the model
            # server when the actual cause is in the payload - most often a
            # prompt longer than the context the model was loaded at.
            return _step(
                _failure(f"local model '{model}' returned no content", _explain(response)),
                "", model, started, usage,
            )
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


# One shape for every answer, in the chat and in the Word report alike: the
# answer itself first, then only the sections the request needs, always in
# this order.
_ANSWER_SHAPE = (
    "\n\nFORMAT\n"
    "Open with the direct answer to the request in one to three plain sentences: no "
    "title, no heading, and no preamble such as \"Deliverable:\" or \"Here is\". Then add "
    "only the sections the request needs, as ### headings, in this order:\n"
    "### Details - the supporting facts, figures and working\n"
    "### What to do - the actions, as a numbered list\n"
    "### Limits - assumptions, and anything the sources do not settle\n"
    "Use short paragraphs and lists, and a table only for three or more comparable rows. "
    "No horizontal rules, no closing summary and no sign-off such as \"End of deliverable\"."
)

_RULE_LINE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
# A line that is nothing but bold text: a heading in all but name.
_BOLD_LINE = re.compile(r"^\s*(?:\*\*|__)\s*(.+?)\s*(?:\*\*|__)\s*:?\s*$")
_TITLE_LINE = re.compile(r"^[*_\s]*(?:final\s+)?deliverable\b\s*[:\-\u2013\u2014]", re.I)
_SIGN_OFF = re.compile(
    r"^[*_\s]*(?:end of (?:the )?(?:deliverable|report|document|response)\b"
    r"|(?:this|the above) (?:deliverable|document|report|response) (?:was|has been|is) "
    r"(?:prepared|produced|generated|compiled)\b"
    r"|(?:prepared|produced|generated) by (?:jarvis|4ce)\b)",
    re.I,
)


def _tidy(text: str) -> str:
    """The answer with the clutter a small model adds taken out.

    What goes: a title line ("**Deliverable: ...**", or an opening # heading),
    horizontal rules, and sign-offs ("End of deliverable.", "This report was
    prepared by ..."). What changes: # and ## headings become ###, and a line
    that is only bold text becomes the ### heading it stands for, unless it
    reads as a label and value ("**Verdict: FAIL**") or a sentence. Blank
    lines are collapsed. Fenced code is left exactly as written.
    """
    parts = re.split(r"(```[\s\S]*?```)", text.strip())
    opening = True  # nothing but blank lines so far
    for i in range(0, len(parts), 2):
        kept = []
        for line in parts[i].split("\n"):
            bare = line.strip()
            if not bare:
                kept.append("")
                continue
            if _RULE_LINE.match(bare) or _SIGN_OFF.match(bare):
                continue
            heading = _HEADING_LINE.match(bare)
            bold = None if heading else _BOLD_LINE.match(bare)
            if opening:
                opening = False
                if _TITLE_LINE.match(bare) or (heading and len(heading.group(1)) <= 2) or bold:
                    continue  # a title: the question above, or the report's cover, names it
            if heading:
                level = max(3, len(heading.group(1)))
                words = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", heading.group(2).strip("*_ "))
                line = "#" * level + " " + words.rstrip(":")
            elif bold:
                words = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", bold.group(1).strip("*_ "))
                label = re.search(r"\S:\s+\S", words)
                if not label and not words.endswith((".", "!", "?")) and len(words) <= 70:
                    line = "### " + words.rstrip(":")
            kept.append(line.rstrip())
        parts[i] = "\n".join(kept)
        if i + 1 < len(parts):
            opening = False
    out = "".join(parts)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


_CITE_RULE = (
    "\n\nThe passages above are numbered by the document they come from, like [1]. "
    "After every finding that rests on a passage, put that number in square brackets "
    "straight after it - for example \"Leakage above 5 drops per minute requires a "
    "shutdown [1].\" Use only these numbers: {numbers}. A finding the passages do not "
    "state gets no number and is labelled as an assumption."
)


def _number_sources(passages: list[dict]) -> tuple[list[dict], str]:
    """Group retrieved passages by the document they came from and number the
    documents in order of first appearance. The chat numbers its citation chips
    the same way - one per distinct source name - so [n] in an answer opens
    exactly the document the agent was shown as [n]."""
    sources: list[dict] = []
    by_name: dict[str, dict] = {}
    blocks: list[str] = []
    for passage in passages:
        source = by_name.get(passage["name"])
        if source is None:
            source = {"name": passage["name"], "passages": []}
            by_name[passage["name"]] = source
            sources.append(source)
        source["passages"].append(passage)
        n = sources.index(source) + 1
        blocks.append(f"[{n}] {passage['name']}\n{passage['text']}")
    return sources, "\n\n---\n\n".join(blocks)


def _source_numbers(sources: list[dict]) -> str:
    return ", ".join(f"[{n}]" for n in range(1, len(sources) + 1))


async def _emit_source(emitter, source: dict) -> None:
    """One document and the passages 4CE retrieved from it, in the shape the
    chat's citation panel reads."""
    if not emitter:
        return
    passages = source["passages"]
    file_id = next((p["meta"].get("file_id") for p in passages if p["meta"].get("file_id")), None)
    await emitter({
        "type": "source",
        "data": {
            "source": {"name": source["name"], "id": file_id or source["name"]},
            "document": [p["text"] for p in passages],
            "metadata": [
                {**{k: v for k, v in p["meta"].items() if isinstance(v, (str, int, float, bool))},
                 "name": source["name"], "source": source["name"]}
                for p in passages
            ],
            "distances": [p["distance"] for p in passages if p["distance"] is not None],
        },
    })


_BRACKETED = re.compile(r"(\s*)\[(\d+(?:\s*,\s*\d+)*)\]")


def _citation(group: str) -> list[int]:
    """The source numbers in a bracketed group - or none, if it is not a citation.

    A citation is one to four source numbers in ascending order: [1], [1, 2].
    Anything else in square brackets is data the answer is about. Read as
    citations, "the median of [5, 3, 9, 1, 7]" named five sources that do not
    exist, the list was replaced with "(unverified)" twice in one sentence, and
    ULTRON - correctly - failed the answer for talking about unverified terms.
    """
    numbers = [int(n) for n in re.split(r"\s*,\s*", group)]
    if len(numbers) > 4 or numbers != sorted(set(numbers)):
        return []
    return numbers


def _citations(text: str) -> list[int]:
    """Every source number cited in a piece of text, in order of appearance."""
    return [n for m in _BRACKETED.finditer(text or "") for n in _citation(m.group(2))]


def _strip_citations(text: str, repl: str = " ") -> str:
    """The text without its citations; data in square brackets stays."""
    return _BRACKETED.sub(lambda m: repl if _citation(m.group(2)) else m.group(0), text or "")


def _check_citations(text: str, count: int) -> str:
    """Keep a bracketed source number only if it names a retrieved document.

    A model can write [3] when two documents were retrieved, or cite at all
    when none were. Shown as a chip, that would point at nothing while looking
    like evidence. So a number that names no retrieved document is dropped, and
    a claim left with none is marked *(unverified)* - the reader sees that it
    was presented as sourced and is not. Code is left alone: [1] there is
    Python.
    """
    def fix(match: re.Match) -> str:
        numbers = _citation(match.group(2))
        if not numbers:
            return match.group(0)
        keep = [str(n) for n in numbers if 1 <= n <= count]
        return f"{match.group(1)}[{', '.join(keep)}]" if keep else " *(unverified)*"

    parts = re.split(r"(```[\s\S]*?```|`[^`\n]*`)", text)
    for i in range(0, len(parts), 2):
        parts[i] = _BRACKETED.sub(fix, parts[i])
    return "".join(parts)


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


# A question names its subject between the question word and the verb it
# asks about: "What does | clause 2.1 of SOP-MEC-014 | require?"
_TITLE_ASK = re.compile(
    r"^(?:what|which|how|why|when|where|who)\s+"
    r"(?:(?:is|are|was|were|does|do|did|can|could|should|would|will|must)\s+)?"
    r"(?:(?:the|a|an|we|i|you|it)\s+)?",
    re.I,
)
_TITLE_VERB = re.compile(
    r"\s+(?:require|requires|say|says|state|states|specify|specifies|mean|means|"
    r"cover|covers|allow|allows|recommend|recommends)\b.*$",
    re.I,
)


_TITLE_BREAKS = ("what", "how", "when", "why", "whether", "which", "who", "where", "if", "also")
_TITLE_DANGLING = ("and", "or", "of", "the", "a", "an", "to", "for", "in", "on", "under", "with", "by", "at", "what", "how")


def _document_title(prompt: str) -> str:
    """A short title describing the deliverable, not the request for it.

    The whole prompt used to become both the heading and the filename, which
    gave documents called `What_is_the_acceptable_mechanical_seal_leakage_rate
    _under_SO.docx` - truncated mid-word, and phrased as a question the
    document answers rather than as its subject. Numbers keep their dots, so
    "clause 2.1" does not become "clause 2 1".
    """
    cleaned = re.sub(r"\s+", " ", prompt or "").strip()
    if not cleaned:
        return "4CE deliverable"
    # A request often states its subject after a colon; prefer what precedes it.
    head = cleaned.split(":", 1)[0]
    first = re.split(r"(?<=[.?!])\s+", head)[0].rstrip(" ?.!")
    asked = _TITLE_ASK.sub("", first)
    if asked != first:
        asked = _TITLE_VERB.sub("", asked)
    words = re.findall(r"[A-Za-z0-9-]+(?:\.[0-9]+)*", asked)
    while words and words[0].lower() in _REQUEST_OPENERS + ("and", "run", "execute"):
        words.pop(0)
    # A request that asks two things ("the leakage limit, and what must happen
    # if it is exceeded") is titled by the first. Cutting at a fixed word count
    # instead ended titles mid-phrase: "... under SOP-MEC-014 and what".
    for i, word in enumerate(words[1:], 1):
        if word.lower() in ("and", "or", "then") and i + 1 < len(words) and words[i + 1].lower() in _TITLE_BREAKS:
            words = words[:i]
            break
    if len(words) > 10:
        words = words[:10]
        while words and words[-1].lower() in _TITLE_DANGLING:
            words.pop()
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


# A verdict line: PASS or FAIL in capitals at the start of a line, allowing
# the markdown a model wraps it in and a "Verdict:" label.
_VERDICT_LINE = re.compile(r"^[\s>*#_`-]*(?:verdict\s*[:-]\s*)?[*_`]*(PASS|FAIL)\b", re.I)


def _parse_verdict(raw: str) -> dict:
    """ULTRON's verdict, its concerns, and a one-line summary of them.

    ULTRON is told to put PASS or FAIL on the first line, and that line wins
    when it is there. A small reasoning model often thinks out loud first
    instead - "Okay, let me try to figure out what's going on here..." - and
    ends with its verdict; that used to count as FAIL whatever it concluded,
    sending the work round a replan for nothing, and its musing became the
    objection shown to the reviewer. So: the first line's verdict, otherwise
    the last one given. No verdict at all still fails closed, and says so.
    """
    text = (raw or "").strip()
    if text.startswith(_ERR):
        return {"status": "ERROR", "passed": False, "detail": text, "summary": "the verifier could not run"}
    lines = text.splitlines()
    hits = [(i, m.group(1).upper()) for i, line in enumerate(lines) if (m := _VERDICT_LINE.match(line))]
    if not hits:
        return {
            "status": "FAIL",
            "passed": False,
            "detail": text[:1500] or "Verifier returned nothing.",
            "summary": "ULTRON gave no PASS or FAIL verdict",
        }
    index, word = hits[0] if hits[0][0] == 0 else hits[-1]
    passed = word == "PASS"
    # Whatever follows the verdict on its own line is the verdict's reason.
    remainder = _VERDICT_LINE.sub("", lines[index], count=1).strip(" *_:-—–")
    after = ([remainder] if remainder else []) + [l for l in lines[index + 1:] if l.strip()]
    before = [l for l in lines[:index] if l.strip()]
    concerns = "\n".join(after or before).strip()
    return {
        "status": word,
        "passed": passed,
        "detail": (concerns or text)[:1500],
        "summary": _clip(re.sub(r"^[\s>*#_`\-\d.)]+", "", after[0]).replace("**", "")) if after else "",
    }


_CHECK_LINE = re.compile(
    r"^[\s>*\-\u2022\d.)]*(OK|PROBLEM|UNVERIFIED|NOT VERIFIED)\b\s*[:\-\u2014\u2013]\s*(.+)$", re.I
)


_SOURCE_GUESS = re.compile(
    r"\b(?:in|from|per|based on|supported by|found in|backed by)\s+(?:any|the|a|its)\s+(?:source|document|passage)s?\b"
    # "... but the source says", "the source document [1] does not mention"
    r"|\bthe (?:original )?(?:source|document|passage|SOP(?:-[\w-]+)?)s?(?: document)?(?:\s*\[\d+\])?\s+"
    r"(?:says|say|states|state|does not|do not|doesn't|only|mentions|lists|defines|uses)\b",
    re.I,
)
# A PROBLEM the verifier takes back in the same line ("... so there is no
# issue here") is not a problem; one that only says the answer leaves
# something open ("does not specify whether") is a question, not an error.
_CONCEDED = re.compile(
    r"\b(?:no (?:issue|problem|contradiction)s?\b|not (?:a )?(?:problem|contradict\w*|an issue)|"
    r"(?:is|are) (?:technically )?(?:correct|valid|consistent|equivalent|accurate)\b|"
    r"technically correct|both are equivalent|clear and explicit|which is correct)",
    re.I,
)
_OPEN_QUESTION = re.compile(
    r"\b(?:does not (?:specify|define|say|state|indicate|clarify)|not specified|unclear whether|"
    r"no indication (?:of )?whether|without clarification)\b",
    re.I,
)
_NEGATION = re.compile(
    r"\b(?:not (?:in|found|present|supported|stated|mentioned|given|listed)|no source|missing|"
    r"unsupported|absent|does not appear|cannot be verified|could not be verified)\b",
    re.I,
)


# A figure, but not the digits of a code like SOP-MEC-014.
_FIGURE = re.compile(r"(?<![\w.\-])\d+(?:[.,]\d+)?(?![\w])")


def _doc_label(name: str) -> str:
    """A document as a reader names it: its code ("SOP-MEC-014") when the
    file name starts with one, else the file name without extension."""
    stem = name.rsplit(".", 1)[0]
    code = re.match(r"[A-Z]{2,}(?:-[A-Z0-9]+)*-\d+", stem)
    return code.group(0) if code else stem.replace("_", " ")


def _figure_checks(deliverable: str, sources: list[dict]) -> list[dict]:
    """4CE's own check, made without a model: every figure in a sentence that
    cites [n] must appear in document n. A model can write "within 30 days
    [1]" when the document says 14; this catches that, and says so."""
    if not sources:
        return []
    texts = {n: " ".join(p["text"] for p in src["passages"]) for n, src in enumerate(sources, 1)}
    prose = re.sub(r"```[\s\S]*?```|`[^`\n]*`", " ", deliverable or "")
    found: list[str] = []
    missing: list[tuple[str, str]] = []
    for sentence in re.split(r"(?<=[.!?])\s+", prose):
        cited = _citations(sentence)
        cited = [n for n in cited if n in texts]
        if not cited:
            continue
        bare = _strip_citations(sentence)
        for figure in _FIGURE.findall(bare):
            pattern = re.compile(rf"(?<![\w.]){re.escape(figure)}(?![\w])")
            if any(pattern.search(texts[n]) for n in cited):
                if figure not in found:
                    found.append(figure)
            else:
                names = ", ".join(_doc_label(sources[n - 1]["name"]) for n in cited)
                missing.append((figure, names))
    checks: list[dict] = []
    if found and not missing:
        figures = ", ".join(found[:6]) + ("…" if len(found) > 6 else "")
        checks.append({
            "kind": "ok",
            "text": f"Every figure the answer cites ({figures}) appears in the source it cites",
            "by": "4CE",
        })
    for figure, names in missing[:4]:
        checks.append({
            "kind": "problem",
            "text": f"{figure} is cited to {names}, which does not contain it",
            "by": "4CE",
        })
    return checks


def _parse_checks(detail: str) -> list[dict]:
    """ULTRON's checks, one per line: what it confirmed, what it objects to,
    and what it could not check. Lines in any other shape are left out, so
    the chat's card only ever shows a check ULTRON actually stated."""
    checks: list[dict] = []
    for line in (detail or "").splitlines():
        match = _CHECK_LINE.match(line.replace("**", "").replace("`", ""))
        if not match:
            continue
        word = match.group(1).upper()
        kind = "ok" if word == "OK" else "problem" if word == "PROBLEM" else "unverified"
        # "OK: the deadline is not in any source" says it passed and failed at
        # once. A small verifier writes that; shown with a tick it misleads.
        if kind == "ok" and _NEGATION.search(match.group(2)):
            kind = "unverified"
        text = _clip(match.group(2).strip(), 180)
        # ULTRON is not shown the retrieved passages (a 1.7B verifier handed
        # three thousand characters of them stopped giving a verdict), so it
        # cannot know what they contain. Its guesses about that are left out;
        # 4CE's own figure check is what speaks to sourcing.
        if _SOURCE_GUESS.search(text):
            continue
        # A verifier that runs out of words mid-line leaves "whether the 3";
        # a fragment says nothing, so it is not shown as a check.
        if len(text.split()) < 4:
            continue
        if kind == "problem" and _CONCEDED.search(text):
            continue
        if kind == "problem" and _OPEN_QUESTION.search(text):
            kind = "unverified"
        # The same line twice says nothing new.
        if any(c["text"] == text for c in checks):
            continue
        # "PROBLEM: none" on a PASS is not a problem.
        if not text or text.lower().strip(" .!") in ("none", "nothing", "n/a", "no problems", "no issues", "no concerns", "none found"):
            continue
        checks.append({"kind": kind, "text": text, "by": "ULTRON"})
    return checks[:8]


def _supporting_text(text: str, figures: set[str]) -> str:
    """The clauses of a retrieved passage that hold the figures an answer
    cites to it: what "[1]" actually rests on. A clause is a numbered line and
    the lines that continue it. With nothing to match, the passage as is."""
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if not line.strip() or re.match(r"^\s*\d+(?:\.\d+)*\s", line):
            if current:
                blocks.append(" ".join(current))
                current = []
        if line.strip():
            current.append(line.strip())
    if current:
        blocks.append(" ".join(current))
    # A clause's own number ("5." or "2.1") is not one of its figures.
    hits = [
        block for block in blocks
        if any(
            re.search(rf"(?<![\w.]){re.escape(f)}(?!\w|\.\d)", re.sub(r"^\s*\d+(?:\.\d+)*\.?\s+", "", block))
            for f in figures
        )
    ]
    return "\n".join(hits) if hits else text


def _cited_figures(text: str, count: int) -> dict[int, set[str]]:
    """The figures each source is cited for, sentence by sentence."""
    found: dict[int, set[str]] = {}
    prose = re.sub(r"```[\s\S]*?```|`[^`\n]*`", " ", text or "")
    for sentence in re.split(r"(?<=[.!?])\s+", prose):
        numbers = _citations(sentence)
        figures = set(_FIGURE.findall(_strip_citations(sentence)))
        for n in numbers:
            if 1 <= n <= count:
                found.setdefault(n, set()).update(figures)
    return found


def _cited_numbers(text: str, count: int) -> list[int]:
    """The source numbers an answer actually cites, in order."""
    return sorted({n for n in _citations(text) if 1 <= n <= count})


_ASKS_FOR_OUTPUT = re.compile(r"\b(?:print|prints|printed|output|outputs|show|display)\b", re.I)


def _execution_check(code: str, report: str, prompt: str = "") -> dict:
    """4CE's own check on generated code: did it run, and did it finish cleanly.

    Read from the sandbox tool's report, so it is what actually happened. The
    program is asked to assert its own result, so a clean exit also means its
    checks held; a failed assert exits non-zero like any other error.
    """
    if not code:
        return {"kind": "problem", "by": "4CE",
                "text": "There is no ```python block in the result, so nothing could be run"}
    if not report or report.startswith(_ERR):
        return {"kind": "unverified", "by": "4CE", "final": True,
                "text": "The code was not executed: the sandbox tool is not attached to this model"}
    if "was NOT executed" in report:
        reason = re.search(r"Reason:\s*(.+)", report)
        return {"kind": "unverified", "by": "4CE", "final": True,
                "text": _clip("The code was not executed" + (f": {reason.group(1).strip()}" if reason else ""), 180)}
    if "**Timed out**" in report:
        return {"kind": "problem", "by": "4CE",
                "text": "The code did not finish inside the sandbox's time limit"}
    exit_code = re.search(r"- Exit code:\s*(-?\d+|None)", report)
    exit_code = exit_code.group(1) if exit_code else "unknown"
    if exit_code == "0":
        # Asked to print, printed nothing: the answer's "Output: 5" was written,
        # not produced. Seen exactly so - a function called and its result
        # dropped - with a made-up output block beneath it.
        if _ASKS_FOR_OUTPUT.search(prompt or "") and "**stdout**" not in report:
            return {"kind": "problem", "by": "4CE",
                    "text": "The request asks for the result to be printed, and the program printed nothing"}
        asserts = len(re.findall(r"^\s*assert\b", code, re.M))
        if asserts:
            return {"kind": "ok", "by": "4CE", "text":
                    f"The code ran in the sandbox and exited 0, with its {asserts} assertion"
                    f"{'' if asserts == 1 else 's'} holding"}
        # Running cleanly is not the same as being right. Shown as a tick it
        # read as a pass; it is something nobody checked.
        return {"kind": "unverified", "by": "4CE",
                "text": "The code ran in the sandbox and exited 0, but asserts nothing about its own result"}
    stderr = re.search(r"\*\*stderr\*\*\s*```\s*\n(.*?)```", report, re.S)
    last = [line for line in (stderr.group(1) if stderr else "").splitlines() if line.strip()]
    return {"kind": "problem", "by": "4CE", "text": _clip(
        f"The code failed in the sandbox with exit code {exit_code}"
        + (f": {last[-1].strip()}" if last else ""), 180,
    )}


def _reservations_phrase(verdict: dict, lead: str, tail: str = "") -> str:
    """", with 2 reservations" - or nothing, for a clean pass or any fail."""
    count = int(verdict.get("reservations") or 0) if verdict.get("passed") else 0
    if not count:
        return ""
    return f"{lead}{count} reservation{'' if count == 1 else 's'}{tail}"


def _egress_mark() -> dict | None:
    """Where the backend's egress watch stands as a run starts.

    The watch lives in the backend (open_webui/utils/fource_egress.py); a
    backend without it simply leaves the run unobserved.
    """
    try:
        from open_webui.utils.fource_egress import watch
        return watch.mark()
    except Exception:
        return None


def _egress_since(mark: dict | None) -> dict:
    """What the workbench's processes were seen connecting to since the mark."""
    try:
        from open_webui.utils.fource_egress import watch
        return watch.since_mark(mark)
    except Exception:
        return {"observed": False, "reason": "this backend has no egress watch"}


def _egress_row(egress: dict | None) -> str:
    if not egress or not egress.get("observed"):
        return "not observed — " + ((egress or {}).get("reason") or "the egress watch is not running")
    external = egress.get("external", 0)
    text = (
        f"**{external}** external connection{'' if external == 1 else 's'} observed across "
        f"{egress.get('processes', 0)} workbench processes during this run "
        f"({egress.get('samples', 0):,} samples, every {egress.get('interval_ms', 0)} ms)"
    )
    lan_out = egress.get("lan_out", 0)
    if lan_out:
        text += f" · {lan_out} other outbound LAN connection{'' if lan_out == 1 else 's'}"
    return text


def _receipt(task_type: str, model_id: str, verdict: dict, approval: str, elapsed: float,
             attempts: int, agent_models: dict, tools_used: list[str] | None,
             sources: list[dict], approver: str = "", approved_at: str = "",
             fingerprint: str = "", steps: list[dict] | None = None,
             signals: list[str] | None = None, egress: dict | None = None) -> str:
    """One line the chat draws as a strip of facts under the answer - where it
    ran, what it stood on, how it was checked, who released it - with ULTRON's
    checks beneath. A fenced block, so any other client shows readable JSON."""
    data = {
        "v": 1,
        "task": task_type,
        "model": model_id.rsplit("/", 1)[-1],
        "agents": {agent: model.rsplit("/", 1)[-1] for agent, model in agent_models.items()},
        "sources": [source["name"] for source in sources],
        # Which of them the answer actually cites: two retrieved and one
        # cited should not read as "grounded in 2 sources".
        "cited": _cited_numbers(verdict.get("cited_text", ""), len(sources)),
        "verdict": str(verdict.get("status", "n/a")).upper(),
        "reservations": verdict.get("reservations", 0),
        "failed_by": verdict.get("failed_by", ""),
        "failed_on": verdict.get("failed_on", ""),
        "attempts": attempts,
        "checks": verdict.get("checks") or _parse_checks(verdict.get("detail", "")),
        "approval": approval,
        "approver": approver,
        "approved_at": approved_at,
        "seconds": round(elapsed),
        "tools": list(tools_used or []),
        # Observed by the backend's egress watch over this run, or None when
        # nothing was watching: an unmeasured run gets no number, not a zero.
        "external_calls": (egress or {}).get("external") if (egress or {}).get("observed") else None,
        "egress": egress or {"observed": False},
        "fingerprint": fingerprint,
        # For the audit record: when the run finished, why TONY routed it as
        # it did, and every step in order.
        "at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "signals": list(signals or []),
        "steps": [
            {
                "agent": step["agent"],
                "label": step.get("label", ""),
                "model": str(step.get("model") or "").rsplit("/", 1)[-1],
                "seconds": round(float(step.get("seconds") or 0), 1),
            }
            for step in (steps or [])
        ],
    }
    if verdict.get("revision"):
        data["revision"] = verdict["revision"]
    return "```4ce-receipt\n" + json.dumps(data, ensure_ascii=False) + "\n```"


_REPORT_LINE = re.compile(
    r"^\*\*(?P<kind>[^*]+)\*\* · (?P<title>.+?) · (?P<kb>\d+) KB, stored on this machine · "
    r"\[Download [^\]]*\]\((?P<url>[^)\s]+)\)(?P<rest>[\s\S]*)$"
)


def _file_card(line: str) -> str:
    """The report tool's download line as a ```4ce-file block, which the chat
    draws as a card with a download button. A line in any other shape - an
    older tool, or an error - is kept as it is."""
    found = _REPORT_LINE.match(line.strip())
    if not found:
        return line
    card = {
        "kind": found["kind"].strip(),
        "title": found["title"].strip(),
        "kb": int(found["kb"]),
        "url": found["url"],
    }
    rest = found["rest"].strip()
    if rest:
        card["note"] = rest
    return "```4ce-file\n" + json.dumps(card, ensure_ascii=False) + "\n```"


_STOP_WORDS = frozenset(
    "the and for are but not with this that from into than then there their they "
    "what when where which while will would should could must does did has have had "
    "was were been being its any all per only also more most such other some each "
    "answer result says said state states stated source sources document".split()
)


def _units(text: str) -> list[str]:
    """An answer as the pieces a change is shown in: one per sentence, with
    the markdown, citation numbers and table rules taken off."""
    units: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            continue
        line = re.sub(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*)", "", line)
        line = line.replace("**", "").replace("__", "")
        line = _strip_citations(line, "").replace("*(unverified)*", "")
        if set(line.strip()) <= set("-|: "):
            continue
        line = " · ".join(cell.strip() for cell in line.strip().strip("|").split("|") if cell.strip())
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"\u201c(])", line):
            # A list marker left on its own ("a.", "3.") is not a change.
            if len(re.findall(r"[A-Za-z]{2,}", sentence)) >= 2:
                units.append(sentence.strip())
    return units


def _words(text: str) -> set[str]:
    """The words that carry meaning, with their endings folded, so "exceeds"
    and "exceeded" count as the same word."""
    words = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) > 2 and w not in _STOP_WORDS:
            words.add(re.sub(r"(?:ing|ed|es|s)$", "", w) if len(w) > 4 else w)
    return words


def _revision(first: dict, after: str, verdict: dict) -> dict:
    """What try 2 changed, and which change answers which objection.

    The two drafts are compared sentence by sentence. Within a changed stretch
    each removed sentence is paired with the added one most like it, so a
    rewording reads as one change, not a deletion and an addition. Each
    objection is then matched to the changes that share its rarer words -
    "exceeded" counts for more than "drops per minute", which every change
    mentions - and a change nothing points to is listed as "also changed".
    """
    a, b = _units(first["draft"]), _units(after)
    changes: list[dict] = []
    same = lambda x, y: re.sub(r"\W+", "", x.lower()) == re.sub(r"\W+", "", y.lower())
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        removed, added, used = a[i1:i2], b[j1:j2], set()
        for gone in removed:
            best, score = None, 0.0
            for k, new in enumerate(added):
                if k not in used:
                    ratio = difflib.SequenceMatcher(a=gone, b=new).ratio()
                    if ratio > score:
                        best, score = k, ratio
            if best is not None and score >= 0.45:
                used.add(best)
                if not same(gone, added[best]):
                    changes.append({"removed": gone, "added": added[best], "kind": "reworded"})
            else:
                changes.append({"removed": gone, "added": "", "kind": "removed"})
        changes += [{"removed": "", "added": new, "kind": "added"} for k, new in enumerate(added) if k not in used]

    # A fix is judged mostly by what try 2 added; what it took out counts half.
    added_words = [_words(c["added"]) for c in changes]
    removed_words = [_words(c["removed"]) for c in changes]
    spread: dict[str, int] = {}
    for words in added_words + removed_words:
        for w in words:
            spread[w] = spread.get(w, 0) + 1
    objections, fixed = [], []
    for text, by in first["objections"]:
        wanted = _words(text)
        scored = sorted(
            (
                (
                    sum(1 / spread[w] for w in wanted & added_words[i])
                    + 0.5 * sum(1 / spread[w] for w in wanted & removed_words[i] - added_words[i]),
                    i,
                )
                for i in range(len(changes))
            ),
            reverse=True,
        )
        fixes = [i for score, i in scored[:2] if score >= 0.25]
        fixed += [i for i in fixes if i not in fixed]
        objections.append({"text": _clip(text, 220), "by": by, "fixes": fixes})

    # The changes an objection points to come first; the list is capped, so
    # the ones that matter are never the ones cut.
    order = fixed + [i for i in range(len(changes)) if i not in fixed]
    keep = order[:14]
    place = {old: new for new, old in enumerate(keep)}
    for objection in objections:
        objection["fixes"] = [place[i] for i in objection["fixes"] if i in place]
    return {
        "objections": objections,
        "changes": [
            {**changes[i], "removed": _clip(changes[i]["removed"], 240), "added": _clip(changes[i]["added"], 240)}
            for i in keep
        ],
        "more": max(0, len(changes) - len(keep)),
        "by": first["failed_by"],
        "verdict": str(verdict.get("status", "")).upper(),
    }


def _review(deliverable: str, verdict: dict, sources: list[dict], attempts: int) -> dict:
    """What the sign-off panel shows beside the draft: the checks made before
    release, what each cited [n] rests on, and on a second try what changed.
    All of it is already worked out for the answer's card and the report;
    this hands the reviewer the same record before they decide."""
    cited = set(_cited_numbers(deliverable, len(sources)))
    figures = _cited_figures(deliverable, len(sources))
    docs = []
    for n, source in enumerate(sources, 1):
        # The chat's passage panel reads a distance in 0..1 as a match share.
        scores = [p.get("distance") for p in source["passages"]]
        scores = [d for d in scores if isinstance(d, (int, float))]
        best = max(scores) if scores and all(0 <= d <= 1 for d in scores) else None
        docs.append({
            "n": n,
            "name": source["name"],
            "cited": n in cited,
            "passage": _clip(
                _supporting_text("\n".join(p["text"] for p in source["passages"]), figures.get(n, set())),
                700,
            ),
            "match": round(best * 100) if best is not None else None,
        })
    return {
        "checks": [
            {"kind": c["kind"], "text": c["text"], "by": c.get("by", "ULTRON")}
            for c in verdict.get("checks") or []
        ],
        "sources": docs,
        "revision": verdict.get("revision"),
        "tries": attempts,
    }


def _objection(verdict: dict) -> str:
    """What the reviewer is told when a draft failed its check: the problems
    as stated, not the verifier's raw text - which, from a small model, could
    open with "Okay, let me try to figure this out..."."""
    problems = [c for c in verdict.get("checks") or [] if c["kind"] == "problem"]
    who = "4CE's figure check" if verdict.get("failed_by") == "4CE" else "ULTRON"
    if problems:
        return f"{who} objected: " + "; ".join(c["text"].rstrip(".") for c in problems[:3]) + "."
    summary = (verdict.get("summary") or "").strip()
    if summary and not re.match(r"(?i)(okay|ok|so|let me|let's|hmm|first|alright)\b", summary):
        return f"{who} objected: {summary}"
    return f"{who} failed it without stating a usable reason."


def _clip(text: str, limit: int = 90) -> str:
    """A single line, cut at a word boundary."""
    line = re.sub(r"\s+", " ", text or "").strip()
    if len(line) <= limit:
        return line
    return line[: line.rfind(" ", 0, limit)].rstrip(" ,;:") + "…"


def _step(text: str, thinking: str, model: str, started: float,
          usage: dict | None = None) -> dict:
    return {
        "text": text,
        "thinking": thinking,
        "model": model,
        "seconds": time.monotonic() - started,
        "usage": usage or {},
    }


def _explain(payload: Any) -> str:
    """The most useful sentence available about why a model call went wrong.

    Bionic reports a refusal precisely - "request (10258 tokens) exceeds the
    available context size (8192 tokens)" names the problem and the fix. That
    text survives in the response or the exception, and is worth far more to
    whoever is standing in front of the screen than a generic failure.
    """
    seen: list[str] = []

    def dig(node: Any, depth: int = 0) -> None:
        if depth > 4 or len(seen) > 3:
            return
        if isinstance(node, str):
            text = node.strip()
            if text and text not in seen:
                seen.append(text)
            return
        if isinstance(node, dict):
            for key in ("message", "detail", "error", "msg"):
                if key in node:
                    dig(node[key], depth + 1)
            return
        if isinstance(node, list):
            for item in node[:2]:
                dig(item, depth + 1)

    if isinstance(payload, BaseException):
        dig(getattr(payload, "detail", None))
        if not seen:
            seen.append(str(payload).strip())
    else:
        # A refused call comes back as a starlette JSONResponse rather than the
        # usual dict, so the reason is in its encoded body and invisible to
        # anything that only knows how to read a mapping.
        body = getattr(payload, "body", None)
        if isinstance(body, (bytes, bytearray)):
            try:
                dig(json.loads(body.decode("utf-8", "replace")))
            except Exception:
                dig(body.decode("utf-8", "replace"))
        dig(payload)

    best = next((t for t in seen if t), "")
    # The upstream often nests its own JSON inside the message; the innermost
    # human sentence is the one worth showing.
    match = re.search(r'"message"\s*:\s*"([^"]{10,400})"', best)
    if match:
        best = match.group(1)
    best = " ".join(best.split()).strip()
    return best[:300]


def _approval_message(deliverable: str, verdict: dict, task_type: str, model_id: str) -> str:
    """What the reviewer reads before deciding: the draft itself, then the ask.

    The gate used to show only ULTRON's verdict and a model name, so the person
    approving a deliverable could not see it - the answer is withheld until the
    decision, and a modal hides the page behind it. A human gate is only a gate
    if the human can read what they are releasing, so the full draft goes in.

    It sits in its own scrolling box because the dialog has no overflow of its
    own: a long draft would otherwise push the Confirm button off the screen.
    The dialog renders this as markdown through DOMPurify, which keeps `class`
    and `style`; the colour classes are ones the app already compiles.
    """
    status = str(verdict.get("status", "UNKNOWN")).upper()
    line = f"**ULTRON: {status}** \u00b7 {task_type} task \u00b7 drafted on `{model_id}`"
    objection = _objection(verdict)
    if status != "PASS" and objection:
        line += f"\n\n*{objection}*"
    return (
        f"{line}\n\n"
        '<div class="text-gray-900 dark:text-gray-100 bg-gray-50 dark:bg-gray-900 '
        'border border-gray-200 dark:border-gray-800" '
        'style="max-height:42vh;overflow-y:auto;padding:12px 14px;margin:10px 0 12px;'
        'border-radius:12px;font-size:13.5px;line-height:1.55">\n\n'
        f"{(deliverable or '').strip() or '*(the draft is empty)*'}\n\n"
        "</div>\n\n"
        "This is exactly what will be released. Type **approve** to release it; "
        "anything else, or an empty box, withholds it."
    )


# Known failures, in the order they are worth checking, each with the sentence
# that tells the person at the screen what to do. The wording follows the
# troubleshooting table in 4ce/docs, so the UI and the runbook agree.
_REMEDIES: list[tuple[tuple[str, ...], str]] = [
    (
        ("connect call failed", "cannot connect to host", "connection refused",
         "errno 61", "all connection attempts failed", "server connection error"),
        "The model server isn't reachable on localhost:1234. Start Bionic and turn on "
        "its server (Developer \u2192 Start Server), then send the message again.",
    ),
    (
        ("exceeds the available context", "context size", "context length",
         "maximum context", "too many tokens"),
        "This request is longer than the model's context window. Attach long documents "
        "instead of pasting them, so retrieval sends only the passages that matter.",
    ),
    (
        ("timed out", "timeout"),
        "The model took too long to answer. If answers are slow in general, a model is "
        "probably loaded above 8192 context \u2014 run `python 4ce/preflight.py --fix`.",
    ),
    (
        ("model not found", "no model", "not loaded", "does not exist"),
        "The model this turn was routed to isn't loaded in Bionic. Load qwen3-vl-4b and "
        "qwen3-1.7b, or run `python 4ce/preflight.py --fix`.",
    ),
]


def _remedy(detail: str) -> str:
    """Plain-language cause and fix for a known failure, or "" if unrecognised.

    Leads the error rather than replacing it: the raw detail is still printed
    underneath, so an unfamiliar failure is never hidden behind a guess.
    """
    text = (detail or "").lower()
    for needles, advice in _REMEDIES:
        if any(n in text for n in needles):
            return advice
    return ""


def _failure(what: str, detail: str) -> str:
    """An error line that leads with the fix when one is known."""
    advice = _remedy(detail)
    raw = f"{what}" + (f" \u2014 {detail}" if detail else ".")
    if not advice:
        return f"{_ERR} {raw}"
    return f"{_ERR} {advice}\n\n*Detail: {raw}*"


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
                grounding: str = "", sources: list[dict] | None = None,
                approver: str = "", approved_at: str = "", fingerprint: str = "",
                egress: dict | None = None) -> str:
    """The receipt the chat shows under an answer, then the full provenance
    table and the reasoning behind each decision, folded away."""
    timings = " · ".join(
        f"{s['agent'].title()} {s['seconds']:.0f}s" for s in steps if s.get("seconds")
    )
    rows = _provenance_rows(
        task_type, signals, model_id, rationale, verdict, approval, elapsed, attempts,
        agent_models, tools_used, grounding, timings, egress,
    )
    if fingerprint:
        rows.append(("Fingerprint", f"SHA-256 `{fingerprint}` of the released answer"))
    table = ["| Stage | Detail |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows]
    receipt = _receipt(
        task_type, model_id, verdict, approval, elapsed, attempts, agent_models,
        tools_used, sources or [], approver, approved_at, fingerprint,
        steps=steps, signals=signals, egress=egress,
    )
    return _provenance_rest(steps, attempts, include_thinking, trace, table, receipt)


def _provenance_rows(task_type: str, signals: list[str], model_id: str, rationale: str,
                     verdict: dict, approval: str, elapsed: float, attempts: int,
                     agent_models: dict, tools_used: list[str] | None, grounding: str,
                     timings: str = "", egress: dict | None = None) -> list[tuple[str, str]]:
    """The provenance rows, shared by the chat's table and the Word report."""
    status = verdict.get("status", "n/a")
    rows = [
        ("Task type", f"`{task_type}`" + (f" — matched: {', '.join(signals)}" if signals else " — no strong signal")),
        ("Model routed", f"`{model_id}` — {rationale}"),
        ("Agents", " · ".join(f"{a} `{m}`" for a, m in agent_models.items())),
        ("Verification", f"ULTRON **{status}**" + (f" after {attempts} attempts" if attempts > 1 else "")
         + _reservations_phrase(verdict, " — with ", " it did not count against the result")),
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
        ("Inference", "Local open-weight models"),
        ("Egress", _egress_row(egress)),
    ]
    return rows


def _provenance_rest(steps: list[dict], attempts: int, include_thinking: bool,
                     trace: list[str], table: list[str], receipt: str = "") -> str:
    blocks = [
        "---",
        receipt,
        "<details>\n<summary>Full provenance</summary>\n\n" + "\n".join(table) + "\n</details>",
    ]

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


async def _status(emitter, action: str, description: str, done: bool = False,
                  facts: list[str] | None = None) -> None:
    # `ts` is the server's clock, so the chat's stage rail can show how long
    # each agent actually took - measured, not estimated. The browser stores
    # status entries with the message, so the timings survive a reload.
    if emitter:
        data = {"action": action, "description": description, "done": done, "ts": round(time.time(), 3)}
        # Real details of this stage, which the chat's live status line rolls
        # in among its lines in the agent's voice. Only what this run actually
        # knows - the voice lines are the chat's; the facts are ours.
        facts = [f for f in (facts or []) if f]
        if facts:
            data["facts"] = facts
        await emitter({"type": "status", "data": data})


