from abc import ABC, abstractmethod


class Agent(ABC):
    name = "agent"

    @abstractmethod
    def plan(self, request: str) -> dict: ...

    @abstractmethod
    def execute(self, action: str, payload: str, model: str) -> str: ...

    @abstractmethod
    def validate(self, result: str, model: str) -> dict: ...

    def status(self) -> str:
        return "waiting"

    def result(self):
        return None


class TonyStark(Agent):
    name = "tony"

    def plan(self, request: str) -> dict:
        lowered = request.lower()
        task_type = "code" if any(word in lowered for word in ("code", "script", "program")) else "analysis"
        return {"task": request, "task_type": task_type, "steps": [
            {"agent": "friday", "action": "analyze_request"},
            {"agent": "jarvis", "action": "execute_structured"},
            {"agent": "ultron", "action": "verify_result"},
        ]}

    def replan(self, request: str, challenge: str, model: str) -> dict:
        return {"reason": challenge, "steps": [
            {"agent": "friday", "action": "reanalyze_with_challenge", "model": model},
            {"agent": "jarvis", "action": "execute_structured", "model": model},
            {"agent": "ultron", "action": "verify_result", "model": model},
        ]}

    def execute(self, action, payload, model):
        return payload

    def validate(self, result, model):
        return {"passed": True, "confidence": 1.0, "challenge": "Plan is structurally valid"}


class Friday(Agent):
    name = "friday"

    def __init__(self, provider, knowledge=None):
        self.provider, self.knowledge = provider, knowledge

    def plan(self, request):
        return {"agent": self.name, "action": "analyze_request"}

    def execute(self, action, payload, model):
        if self.knowledge:
            grounded = self.knowledge.answer(payload, self.provider, model)
            if grounded["citations"]:
                citations = "\n".join(f"Source: {item['source']} | page {item['page']} | section {item['section']}" for item in grounded["citations"])
                return grounded["answer"] + "\n\n" + citations
        prompt = ("You are FRIDAY, the analysis agent. Analyze the request below. "
                  "Return factual findings and clearly label assumptions.\n\n" + payload)
        return self.provider.generate(prompt, model)

    def validate(self, result, model):
        return {"passed": bool(result.strip()), "confidence": 0.7 if result.strip() else 0.0}


class Jarvis(Agent):
    name = "jarvis"

    def plan(self, request):
        return {"agent": self.name, "action": "execute_structured"}

    def __init__(self, provider, tools=None):
        self.provider, self.tools = provider, tools

    def execute(self, action, payload, model):
        tool_result = self.tools.execute(payload) if self.tools else None
        return "JARVIS execution result:\n" + ((tool_result + "\n") if tool_result else "") + payload

    def validate(self, result, model):
        return {"passed": bool(result.strip()), "confidence": 0.8 if result.strip() else 0.0}


class Ultron(Agent):
    name = "ultron"

    def __init__(self, provider):
        self.provider = provider

    def plan(self, request):
        return {"agent": self.name, "action": "verify_result"}

    def execute(self, action, payload, model):
        prompt = ("You are ULTRON, a skeptical verification agent. Challenge the result below. "
                  "Respond with exactly PASS or FAIL on the first line, then list concerns and confidence.\n\n" + payload)
        return self.provider.generate(prompt, model)

    def validate(self, result, model):
        raw = result.strip()
        parsed = {}
        if raw.startswith("{"):
            try:
                import json
                parsed = json.loads(raw)
            except (TypeError, ValueError):
                parsed = {}
        first_line = raw.splitlines()[0].upper() if raw else "FAIL"
        status = str(parsed.get("status", "PASS" if first_line.startswith("PASS") else "FAIL")).upper()
        passed = status == "PASS"
        return {"status": status, "passed": passed, "confidence": float(parsed.get("confidence", 0.85 if passed else 0.25)),
                "issues": parsed.get("issues", [] if passed else ["Verifier returned a failure verdict"]),
                "warnings": parsed.get("warnings", []), "evidence": parsed.get("evidence", []),
                "recommendation": parsed.get("recommendation", "approve" if passed else "rework"), "summary": raw[:1000]}


def agents_for(provider, tools=None, knowledge=None):
    return {"tony": TonyStark(), "friday": Friday(provider, knowledge), "jarvis": Jarvis(provider, tools), "ultron": Ultron(provider)}
