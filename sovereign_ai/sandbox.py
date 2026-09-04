import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool = False
    error: str | None = None


class DockerSandbox:
    """Runs generated Python only in a disposable, network-disabled container."""

    def __init__(self, image="multi-llm-docs-sovereign-ai", timeout=30, memory="256m", cpus="1.0", output_limit=100_000):
        self.image, self.timeout, self.memory, self.cpus, self.output_limit = image, timeout, memory, cpus, output_limit

    def available(self):
        return shutil.which("docker") is not None

    def run(self, code, files=None):
        if not self.available(): return SandboxResult(False, "", "", None, error="Docker is required for the code sandbox")
        with tempfile.TemporaryDirectory(prefix="sovereign-sandbox-") as directory:
            source = Path(directory) / "main.py"; source.write_text(code, encoding="utf-8")
            for name, content in (files or {}).items():
                target = (Path(directory) / name).resolve()
                if Path(directory).resolve() not in target.parents: return SandboxResult(False, "", "", None, error="Sandbox file escaped workspace")
                target.parent.mkdir(parents=True, exist_ok=True); target.write_text(content, encoding="utf-8")
            command = ["docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64", "--memory", self.memory, "--cpus", self.cpus, "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", "-v", f"{directory}:/workspace:ro", "-w", "/workspace", "--env", "PYTHONUNBUFFERED=1", self.image, "python", "main.py"]
            try:
                completed = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout, env={"PATH": os.environ.get("PATH", "")})
                return SandboxResult(completed.returncode == 0, completed.stdout[:self.output_limit], completed.stderr[:self.output_limit], completed.returncode)
            except subprocess.TimeoutExpired as exc:
                return SandboxResult(False, (exc.stdout or "")[:self.output_limit], (exc.stderr or "")[:self.output_limit], None, True, "Execution timed out")
            except OSError as exc:
                return SandboxResult(False, "", "", None, error=str(exc))
