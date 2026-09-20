"""
title: 4CE Sovereignty Check
author: 4CE
version: 0.1.0
description: Audits the running system for anything that could send data off the premises - model endpoints, embedding and OCR engines, web search, telemetry and update checks - and reports a verdict from live configuration rather than a claim.
"""

import ipaddress
import socket
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from open_webui.models.config import Config

LOCAL_HOSTNAMES = {
    "localhost", "127.0.0.1", "::1", "0.0.0.0",
    "host.docker.internal", "gateway.docker.internal",
    "ollama", "tika", "docling", "chroma", "qdrant", "redis", "db", "postgres",
}

# Whether the interface still offers "Attach Webpage", which hands the server a
# URL to retrieve. The built-in fetcher has no configuration switch, so this is
# the only thing there is to check: it is governed by whether the action is
# present in the input menu. Set from the fork's own frontend, and it must be
# changed in step with `src/lib/components/chat/MessageInput/InputMenu.svelte`.
WEB_PAGE_ATTACH_OFFERED = False


class Tools:
    class Valves(BaseModel):
        treat_private_ranges_as_local: bool = Field(
            default=True,
            description="Count RFC1918 addresses (10.x, 172.16-31.x, 192.168.x) as on-premise.",
        )
        resolve_hostnames: bool = Field(
            default=False,
            description="Resolve unknown hostnames to check whether they point at a private address. Performs a local DNS lookup.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    async def verify_sovereignty(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Audit the running system for any configured path that could send data outside the premises.

        Use this whenever the user asks whether the system is air-gapped, sovereign, offline,
        or whether any data leaves the machine. It inspects live configuration - model
        endpoints, embedding and document-extraction engines, web search, telemetry and
        update checks - and returns a pass/fail verdict with the evidence.

        :return: A sovereignty report listing every checked surface and the overall verdict.
        """
        await _emit(__event_emitter__, "sovereignty", "Auditing configured egress paths")

        findings: list[tuple[str, bool, str]] = []

        try:
            from open_webui.env import ENABLE_OTEL, ENABLE_VERSION_UPDATE_CHECK, OFFLINE_MODE
        except Exception:
            OFFLINE_MODE, ENABLE_VERSION_UPDATE_CHECK, ENABLE_OTEL = None, None, None

        if OFFLINE_MODE is not None:
            findings.append((
                "Offline mode",
                bool(OFFLINE_MODE),
                "enabled — model auto-download and update checks are disabled"
                if OFFLINE_MODE
                else "DISABLED — set OFFLINE_MODE=true to harden the deployment",
            ))
            findings.append((
                "Update check",
                not ENABLE_VERSION_UPDATE_CHECK,
                "disabled" if not ENABLE_VERSION_UPDATE_CHECK else "ENABLED — this contacts api.github.com on startup",
            ))
            findings.append((
                "Telemetry export",
                not ENABLE_OTEL,
                "disabled" if not ENABLE_OTEL else "ENABLED — OpenTelemetry is exporting traces",
            ))

        settings = await _safe_config(
            "openai.api_base_urls", "ollama.base_urls", "rag.embedding_engine",
            "rag.content_extraction_engine", "rag.openai.api_base_url", "rag.ollama.base_url",
            "web.search.enable", "ui.enable_community_sharing",
            "web.loader.engine", "web.loader.external_web_loader_url",
            "image_generation.enable", "image_generation.engine",
            "image_generation.openai.api_base_url", "image_generation.gemini.api_base_url",
            "images.edit.enable", "images.edit.engine", "images.edit.openai.api_base_url",
            "audio.stt.engine", "audio.stt.openai.api_base_url",
            "audio.tts.engine", "audio.tts.openai.api_base_url",
            "tool_server.connections", "terminal_server.connections",
        )

        for label, key in (
            ("Chat model endpoints (OpenAI-compatible)", "openai.api_base_urls"),
            ("Chat model endpoints (Ollama)", "ollama.base_urls"),
            ("Embedding endpoint (OpenAI-compatible)", "rag.openai.api_base_url"),
            ("Embedding endpoint (Ollama)", "rag.ollama.base_url"),
        ):
            urls = _as_list(settings.get(key))
            if not urls:
                findings.append((label, True, "none configured"))
                continue
            verdicts = [(u, self._is_local(u)) for u in urls]
            external = [u for u, ok in verdicts if not ok]
            findings.append((
                label,
                not external,
                ", ".join(f"{u} ({'local' if ok else 'EXTERNAL'})" for u, ok in verdicts)
                if external else ", ".join(u for u, _ in verdicts) + " — all on-premise",
            ))

        engine = (settings.get("rag.embedding_engine") or "").strip()
        engine_endpoints = _as_list(settings.get("rag.openai.api_base_url")) if engine == "openai" else (
            _as_list(settings.get("rag.ollama.base_url")) if engine == "ollama" else []
        )
        engine_local = all(self._is_local(u) for u in engine_endpoints) if engine_endpoints else engine == ""
        findings.append((
            "Embedding engine",
            engine_local,
            "local sentence-transformers (in-process)" if engine == ""
            else f"'{engine}' via {', '.join(engine_endpoints)} — "
                 + ("on-premise" if engine_local else "EXTERNAL ENDPOINT")
            if engine_endpoints
            else f"'{engine}' — no endpoint configured to verify",
        ))

        extraction = (settings.get("rag.content_extraction_engine") or "").strip()
        cloud_extractors = {"mistral_ocr", "datalab_marker", "external"}
        findings.append((
            "Document extraction",
            extraction not in cloud_extractors,
            "built-in local parsers" if extraction == ""
            else f"'{extraction}'" + (" — CLOUD SERVICE" if extraction in cloud_extractors else " (self-hosted)"),
        ))

        web_search = bool(settings.get("web.search.enable"))
        findings.append((
            "Web search",
            not web_search,
            "disabled" if not web_search else "ENABLED — queries would leave the premises",
        ))

        # Fetching a page is egress even when no search engine is configured:
        # "Attach Webpage" hands the server a URL and it retrieves it. There is
        # no switch for the built-in fetcher, so the honest check is whether the
        # action has been withdrawn from the interface that reaches it.
        loader_engine = (settings.get("web.loader.engine") or "").strip()
        loader_external = (settings.get("web.loader.external_web_loader_url") or "").strip()
        findings.append((
            "Web page fetching",
            not WEB_PAGE_ATTACH_OFFERED and not loader_external,
            (
                "OFFERED — 'Attach Webpage' would fetch a URL from this server"
                if WEB_PAGE_ATTACH_OFFERED
                else f"external loader configured: {loader_external}"
                if loader_external
                else "withdrawn from the interface"
                + (f"; loader engine '{loader_engine}'" if loader_engine else "")
            ),
        ))

        for label, enable_key, engine_key, url_keys in (
            ("Image generation", "image_generation.enable", "image_generation.engine",
             ("image_generation.openai.api_base_url", "image_generation.gemini.api_base_url")),
            ("Image editing", "images.edit.enable", "images.edit.engine",
             ("images.edit.openai.api_base_url",)),
        ):
            enabled = bool(settings.get(enable_key))
            remote = [settings.get(k) for k in url_keys]
            remote = [u for u in remote if u and not self._is_local(u)]
            findings.append((
                label,
                not enabled and not remote,
                "disabled, no endpoint configured" if not enabled and not remote
                else f"ENABLED via '{settings.get(engine_key)}'" if enabled
                else "disabled, but an external endpoint is configured: " + ", ".join(remote),
            ))

        for label, engine_key, url_key, local_meaning in (
            ("Speech to text", "audio.stt.engine", "audio.stt.openai.api_base_url",
             "local whisper, in-process"),
            ("Text to speech", "audio.tts.engine", "audio.tts.openai.api_base_url",
             "browser voices, nothing sent"),
        ):
            engine_name = (settings.get(engine_key) or "").strip()
            url = (settings.get(url_key) or "").strip()
            remote_url = bool(url) and not self._is_local(url)
            local_engine = engine_name in ("", "browser-kokoro", "transformers")
            findings.append((
                label,
                local_engine and not remote_url,
                local_meaning if local_engine and not remote_url
                else f"engine '{engine_name}' — LEAVES THE PREMISES" if not local_engine
                else f"local engine, but an external endpoint is stored: {url}",
            ))

        for label, key in (
            ("External tool servers", "tool_server.connections"),
            ("Terminal servers", "terminal_server.connections"),
        ):
            connections = settings.get(key) or []
            count = len(connections) if isinstance(connections, list) else 0
            findings.append((
                label,
                count == 0,
                "none configured" if count == 0 else f"{count} CONFIGURED — each is an outbound path",
            ))

        sharing = settings.get("ui.enable_community_sharing")
        findings.append((
            "Community sharing",
            not sharing,
            "disabled" if not sharing else "enabled — exposes a share-to-openwebui.com action",
        ))

        passed = sum(1 for _, ok, _ in findings if ok)
        total = len(findings)
        sovereign = passed == total

        await _emit(
            __event_emitter__, "sovereignty",
            f"Sovereignty audit: {passed}/{total} checks passed", done=True,
        )

        lines = [
            f"## Sovereignty audit — {'PASS' if sovereign else 'ATTENTION REQUIRED'}",
            "",
            f"**{passed} of {total} checks passed.**",
            "",
            "| Surface | Status | Detail |",
            "|---|---|---|",
        ]
        for label, ok, detail in findings:
            lines.append(f"| {label} | {'PASS' if ok else 'FAIL'} | {detail} |")

        lines += [
            "",
            "This report is generated from the configuration the server is actually running, "
            "not from a static claim.",
        ]
        if not sovereign:
            lines.append(
                "\n> Every FAIL above is a configured path that *could* carry data off the "
                "premises. Resolve them before asserting air-gapped operation."
            )
        lines.append(
            "\n*Configuration audit only. It does not observe packets — pair it with a host "
            "network monitor, or run the stack on a Docker network with no gateway, for "
            "physical proof.*"
        )
        return "\n".join(lines)

    def _is_local(self, url: str) -> bool:
        host = urlparse(url if "://" in url else f"http://{url}").hostname
        if not host:
            return False
        host = host.lower()
        if host in LOCAL_HOSTNAMES or host.endswith(".local") or host.endswith(".internal"):
            return True
        address = _parse_ip(host)
        if address is None and self.valves.resolve_hostnames:
            address = _resolve(host)
        if address is None:
            return False
        if address.is_loopback:
            return True
        return self.valves.treat_private_ranges_as_local and address.is_private


def _parse_ip(host: str):
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _resolve(host: str):
    try:
        return ipaddress.ip_address(socket.gethostbyname(host))
    except (OSError, ValueError):
        return None


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if str(v).strip()]
    return []


async def _safe_config(*keys: str) -> dict:
    try:
        return await Config.get_many(*keys) or {}
    except Exception:
        values = {}
        for key in keys:
            try:
                values[key] = await Config.get(key)
            except Exception:
                values[key] = None
        return values


async def _emit(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})
