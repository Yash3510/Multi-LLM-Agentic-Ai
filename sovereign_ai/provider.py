from abc import ABC, abstractmethod
from typing import Callable, Iterable, Optional


class ModelProvider(ABC):
    """Provider-independent contract for all local inference backends."""

    @abstractmethod
    def chat(self, messages: list[dict], model: str) -> str: ...

    def generate(self, prompt: str, model: str) -> str:
        return self.chat([{"role": "user", "content": prompt}], model)

    @abstractmethod
    def stream(self, messages: list[dict], model: str,
               on_token: Callable[[str], None], stop_event=None) -> str: ...

    def vision(self, prompt: str, image: bytes, model: str) -> str:
        raise NotImplementedError("This provider does not support vision")

    @abstractmethod
    def health_check(self) -> tuple[bool, str]: ...

    @abstractmethod
    def list_models(self) -> Iterable[str]: ...
