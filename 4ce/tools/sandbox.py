"""
title: 4CE Sovereign Sandbox
author: 4CE
version: 0.1.0
description: Executes generated Python inside a disposable, network-disabled container. No network, no writable root, no inherited privileges, hard CPU/memory/PID caps and a wall-clock timeout.
"""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        image: str = Field(
            default="python:3.12-alpine",
            description="Container image used for execution. Must already be present locally for air-gapped operation.",
        )
        timeout_seconds: int = Field(default=30, description="Wall-clock limit for a single run.")
        memory: str = Field(default="256m", description="Hard memory cap.")
        cpus: str = Field(default="1.0", description="CPU quota.")
        pids_limit: int = Field(default=64, description="Maximum processes inside the container.")
        output_limit: int = Field(default=20000, description="Maximum characters returned from stdout/stderr.")

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    async def run_python(
        self,
        code: str,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Execute Python source in an isolated, network-disabled container and return its output.

        Use this whenever code must actually be run and verified rather than merely written.
        The container has no network access, a read-only filesystem, dropped capabilities and
        a hard timeout, so nothing it does can reach the host or the outside world.

        :param code: Complete, self-contained Python source. It runs as __main__; print anything you want returned.
        :return: A report containing the exit status, stdout and stderr.
        """
        if not code or not code.strip():
            return "No code was supplied to execute."

        await _emit(__event_emitter__, "sandbox", "JARVIS: executing in the isolated sandbox")

        available, detail = await _docker_available()
        if not available:
            await _emit(__event_emitter__, "sandbox", "Sandbox unavailable", done=True)
            return (
                "The sovereign sandbox is unavailable, so this code was NOT executed.\n\n"
                f"Reason: {detail}\n\n"
                "The 4CE backend needs the `docker` CLI on its PATH and a reachable daemon. "
                "Run the backend natively on the host (recommended), or mount the Docker socket "
                "into its container."
            )

        result = await self._execute(code)

        status = "completed" if result["exit_code"] == 0 else "failed"
        await _emit(__event_emitter__, "sandbox", f"Sandbox run {status}", done=True)

        report = [
            f"### Sandbox execution: {status}",
            "",
            f"- Image: `{self.valves.image}`",
            f"- Isolation: `--network none`, `--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges`",
            f"- Limits: {self.valves.memory} memory, {self.valves.cpus} CPU, {self.valves.pids_limit} PIDs, {self.valves.timeout_seconds}s wall clock",
            f"- Exit code: {result['exit_code']}",
        ]
        if result["timed_out"]:
            report.append("- **Timed out** before completing.")
        if result["error"]:
            report.append(f"- Error: {result['error']}")
        if result["stdout"]:
            report += ["", "**stdout**", "```", result["stdout"], "```"]
        if result["stderr"]:
            report += ["", "**stderr**", "```", result["stderr"], "```"]
        if not result["stdout"] and not result["stderr"]:
            report += ["", "The program produced no output."]
        return "\n".join(report)

    async def _execute(self, code: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="4ce-sandbox-") as workdir:
            (Path(workdir) / "main.py").write_text(code, encoding="utf-8")
            command = [
                "docker", "run", "--rm",
                "--network", "none",
                "--read-only",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges",
                "--pids-limit", str(self.valves.pids_limit),
                "--memory", self.valves.memory,
                "--cpus", self.valves.cpus,
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
                "-v", f"{workdir}:/workspace:ro",
                "-w", "/workspace",
                "--env", "PYTHONUNBUFFERED=1",
                self.valves.image,
                "python", "main.py",
            ]
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={"PATH": os.environ.get("PATH", "")},
                )
            except OSError as exc:
                return _result(None, "", "", error=str(exc))

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.valves.timeout_seconds
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()
                return _result(None, "", "", timed_out=True, error="Execution exceeded the time limit")

            limit = self.valves.output_limit
            return _result(
                process.returncode,
                stdout.decode("utf-8", "replace")[:limit],
                stderr.decode("utf-8", "replace")[:limit],
            )


def _result(exit_code, stdout: str, stderr: str, timed_out: bool = False, error: str | None = None) -> dict:
    return {
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
        "error": error,
    }


async def _docker_available() -> tuple[bool, str]:
    if shutil.which("docker") is None:
        return False, "the `docker` executable is not on PATH"
    try:
        process = await asyncio.create_subprocess_exec(
            "docker", "info", "--format", "{{.ServerVersion}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=8)
    except (OSError, asyncio.TimeoutError):
        return False, "the Docker daemon did not respond"
    if process.returncode != 0:
        return False, (stderr.decode("utf-8", "replace").strip() or "the Docker daemon is not running")
    return True, stdout.decode("utf-8", "replace").strip()


async def _emit(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})
