import json
import base64
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from .provider import ModelProvider


class OpenAICompatibleProvider(ModelProvider):
    """Provider for Bionic Studio, LM Studio, and similar local APIs."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def chat(self, messages, model):
        result = []
        return self.stream(messages, model, result.append)

    def vision(self, prompt, image, model):
        encoded = base64.b64encode(image).decode("ascii")
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + encoded}},
        ]}], "stream": False}).encode()
        request = Request(self.base_url + "/chat/completions", data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=120) as response:
            return json.load(response)["choices"][0]["message"]["content"]

    def stream(self, messages, model, on_token, stop_event=None):
        body = json.dumps({"model": model, "messages": messages, "stream": True}).encode()
        request = Request(self.base_url + "/chat/completions", data=body,
                          headers={"Content-Type": "application/json"}, method="POST")
        chunks = []
        with urlopen(request, timeout=120) as response:
            for line in response:
                if stop_event is not None and stop_event.is_set():
                    break
                decoded = line.decode("utf-8").strip()
                if not decoded.startswith("data:"):
                    continue
                data = decoded[5:].strip()
                if data == "[DONE]":
                    break
                payload = json.loads(data)
                choices = payload.get("choices", [])
                token = choices[0].get("delta", {}).get("content", "") if choices else ""
                if token:
                    chunks.append(token)
                    on_token(token)
        return "".join(chunks)

    def health_check(self):
        try:
            with urlopen(self.base_url + "/models", timeout=3):
                return True, "Local model API connected"
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            return False, f"Local model API unavailable: {exc.reason if hasattr(exc, 'reason') else 'offline'}"

    def list_models(self):
        try:
            with urlopen(self.base_url + "/models", timeout=3) as response:
                return [item["id"] for item in json.load(response).get("data", [])]
        except (URLError, HTTPError, TimeoutError, OSError, ValueError, KeyError):
            return []
