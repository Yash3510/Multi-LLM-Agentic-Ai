"""
title: 4CE Sovereign Sandbox
author: 4CE
version: 0.1.0
description: Executes generated Python inside a disposable, network-disabled container. No network, no writable root, no inherited privileges, hard CPU/memory/PID caps and a wall-clock timeout.
"""

import asyncio
import io
import json
import mimetypes
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from open_webui.models.files import FileForm, Files
from open_webui.storage.provider import Storage


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
        output_dir: str = Field(
            default="",
            description=(
                "Directory on this machine where files the code writes to /output are also kept, "
                "for example an inspection share. Blank keeps them as downloads only. The "
                "container never sees this path: it writes to a throwaway directory and the "
                "backend copies the results here afterwards."
            ),
        )
        max_output_files: int = Field(
            default=20, description="Most files a single run may return."
        )
        max_output_file_mb: int = Field(
            default=10, description="Largest single returned file, in megabytes."
        )

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    async def run_python(
        self,
        code: str,
        __user__: dict | None = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Execute Python source in an isolated, network-disabled container and return its output.

        Use this whenever code must actually be run and verified rather than merely written.
        The container has no network access, a read-only filesystem, dropped capabilities and
        a hard timeout, so nothing it does can reach the host or the outside world.

        To hand a file back - a spreadsheet, a chart, a report - write it into the
        directory /output. Everything left there is returned to the user as a download.
        Nowhere else is writable, so a file written anywhere else is discarded.

        :param code: Complete, self-contained Python source. It runs as __main__; print anything you want returned. Write any files you want returned into /output.
        :return: A report containing the exit status, stdout, stderr and any files produced.
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
        if not result["stdout"] and not result["stderr"] and not result["produced"]:
            report += ["", "The program produced no output."]

        if result["produced"]:
            report += ["", "**Files produced**", ""] + await self._deliver(
                result["produced"], __user__, __event_emitter__
            )
        return "\n".join(report)

    async def _deliver(
        self,
        produced: list[dict],
        user: dict | None,
        emitter: Callable[[dict], Awaitable[None]] | None,
    ) -> list[str]:
        """Register each produced file for download, and copy it where the operator asked."""
        await _emit(emitter, "sandbox", "Collecting the files the run produced")

        keep = (self.valves.output_dir or "").strip()
        destination: Path | None = None
        lines: list[str] = []
        if keep:
            try:
                destination = Path(keep).expanduser().resolve()
                destination.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                destination = None
                lines.append(f"- Could not use the configured output directory `{keep}`: {exc}")

        for item in produced:
            if item.get("skipped"):
                lines.append("- Not returned: " + ", ".join(item["skipped"]))
                continue

            name = item["name"]
            size_kb = item["size"] // 1024 or 1
            saved = ""
            if destination is not None:
                try:
                    target = destination / Path(name).name
                    await asyncio.to_thread(target.write_bytes, item["bytes"])
                    saved = f" - saved to `{target}`"
                except Exception as exc:
                    saved = f" - could not be saved to the output directory: {exc}"

            link = ""
            if user and user.get("id"):
                file_id = str(uuid.uuid4())
                media = mimetypes.guess_type(name)[0] or "application/octet-stream"
                try:
                    contents, path = await asyncio.to_thread(
                        Storage.upload_file,
                        io.BytesIO(item["bytes"]),
                        f"{file_id}_{Path(name).name}",
                        {},
                    )
                    record = await Files.insert_new_file(
                        user["id"],
                        FileForm(
                            id=file_id,
                            filename=Path(name).name,
                            path=path,
                            data={},
                            meta={"name": Path(name).name, "content_type": media, "size": len(contents)},
                        ),
                    )
                    if record is not None:
                        link = f" - [download](/api/v1/files/{file_id}/content)"
                except Exception as exc:
                    link = f" - could not be registered for download: {exc}"

            lines.append(f"- `{name}` ({size_kb} KB){link}{saved}")

        if destination is None and not keep:
            lines += [
                "",
                "_Set the sandbox tool's `output_dir` valve to also keep these files on this "
                "machine._",
            ]
        return lines

    async def _execute(self, code: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="4ce-sandbox-") as workdir:
            (Path(workdir) / "main.py").write_text(code, encoding="utf-8")
            # A fresh, empty directory per run. The container writes here and
            # nowhere else that survives; it never sees the operator's own path.
            outdir = Path(workdir) / "output"
            outdir.mkdir()
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
                "-v", f"{outdir}:/output:rw",
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
                produced=self._collect(outdir),
            )

    def _collect(self, outdir: Path) -> list[dict]:
        """Read back whatever the run left in /output, largest limits first."""
        cap = self.valves.max_output_file_mb * 1024 * 1024
        produced: list[dict] = []
        skipped: list[str] = []
        for path in sorted(p for p in outdir.rglob("*") if p.is_file()):
            if len(produced) >= self.valves.max_output_files:
                skipped.append(path.name)
                continue
            size = path.stat().st_size
            if size > cap:
                skipped.append(f"{path.name} ({size // (1024 * 1024)} MB, over the limit)")
                continue
            produced.append({
                "name": path.relative_to(outdir).as_posix(),
                "bytes": path.read_bytes(),
                "size": size,
            })
        if skipped:
            produced.append({"name": "", "bytes": b"", "size": 0, "skipped": skipped})
        return produced


def _result(exit_code, stdout: str, stderr: str, timed_out: bool = False, error: str | None = None,
            produced: list[dict] | None = None) -> dict:
    return {
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
        "error": error,
        "produced": produced or [],
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
