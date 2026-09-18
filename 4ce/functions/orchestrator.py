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
            return await self._run_chain(
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
        except asyncio.CancelledError:
            await asyncio.shield(
                self._record_stop(__metadata__, __event_emitter__, trace, steps)
            )
            raise

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

        user = await Users.get_user_by_id(__user__["id"])
        if user is None:
            return "4CE could not resolve the requesting user."

        passages = await self._retrieve(__request__, user, __metadata__, prompt)
        if passages:
            retrieved = f"{retrieved}\n\n{passages}".strip() if retrieved else passages

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
            sop = ""
            if task_type in ("document", "analysis", "vision"):
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
                        trace if self.valves.show_trace else [], agent_models, tools_used, retrieved,
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
            time.monotonic() - started, attempts, self.valves.show_model_thinking,
            trace if self.valves.show_trace else [], agent_models, tools_used, retrieved,
        )

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
    "any action. Do not list the agents unless you are asked what they are; a greeting "
    "deserves a greeting, not an architecture diagram. If you do name them, the names "
    "are exactly TONY, FRIDAY, JARVIS and ULTRON - a small model reciting them from "
    "memory tends to invent spellings, and a garbled name is the first thing a reader "
    "sees."
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

    stem = re.sub("[^A-Za-z0-9]+", "_", title).strip("_")[:50].lower() or "artifact"
    return [(f"{stem}.{suffix}", "\n\n".join(parts)) for suffix, parts in grouped.items()]


def _document_title(prompt: str) -> str:
    """A short, file-safe title taken from the request."""
    cleaned = re.sub("\s+", " ", prompt).strip()
    return cleaned[:70].rstrip(" ,.;:") or "4CE deliverable"


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
                agent_models: dict, tools_used: list[str] | None = None,
                retrieved: str = "") -> str:
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
        (
            "Grounding",
            f"{len(retrieved):,} characters of supplied context reached FRIDAY"
            if retrieved
            else "none - no knowledge base attached, answered from the request alone",
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


