class ModelRouter:
    """Selects local models by task capability, with a safe configured fallback."""

    def __init__(self, provider, default_model: str):
        self.provider = provider
        self.default_model = default_model

    def route(self, task_type: str, preferred: str | None = None) -> str:
        if preferred:
            return preferred
        models = list(self.provider.list_models())
        if not models:
            return self.default_model
        keywords = {"vision": ("vision", "vl"), "code": ("code", "coder")}.get(task_type, ())
        for model in models:
            if any(word in model.lower() for word in keywords):
                return model
        return models[0]
