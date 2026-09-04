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

    def execute(self, action, payload, model):
        return payload

    def validate(self, result, model):
        return {"passed": True, "confidence": 1.0, "challenge": "Plan is structurally valid"}


class Friday(Agent):
    name = "friday"

    def __init__(self, provider):
        self.provider = provider

    def plan(self, request):
        return {"agent": self.name, "action": "analyze_request"}

    def execute(self, action, payload, model):
        prompt = ("You are FRIDAY, the analysis agent. Analyze the request below. "
                  "Return factual findings and clearly label assumptions.\n\n" + payload)
        return self.provider.generate(prompt, model)

    def validate(self, result, model):
        return {"passed": bool(result.strip()), "confidence": 0.7 if result.strip() else 0.0}


class Jarvis(Agent):
    name = "jarvis"

    def plan(self, request):
        return {"agent": self.name, "action": "execute_structured"}

    def execute(self, action, payload, model):
        return "JARVIS execution result:\n" + payload

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
        first_line = result.strip().splitlines()[0].upper() if result.strip() else "FAIL"
        return {"passed": first_line.startswith("PASS"), "confidence": 0.85 if first_line.startswith("PASS") else 0.25, "challenge": result}


def agents_for(provider):
    return {"tony": TonyStark(), "friday": Friday(provider), "jarvis": Jarvis(), "ultron": Ultron(provider)}
