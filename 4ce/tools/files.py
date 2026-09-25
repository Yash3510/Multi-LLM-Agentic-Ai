"""
title: 4CE Workspace Files
author: 4CE
version: 0.1.0
description: Reads, lists and writes files in one workspace folder on this machine - never outside it. Overwriting a file keeps its earlier version, and every read and write is recorded in 4CE's audit trail.
"""

import asyncio
import hashlib
import re
from pathlib import Path

from pydantic import BaseModel, Field

# What 4CE writes into the workspace: text a person or a plant system reads.
# Not "anything the model named": a workspace a model can fill with .exe or
# .bat files is a way in, not a place for work.
WRITABLE = {
    ".txt", ".md", ".csv", ".tsv", ".json", ".yaml", ".yml", ".xml", ".html", ".log",
    ".ini", ".toml", ".py", ".sql",
}
# Kept out of reach even inside the workspace: its history is read, not rewritten.
VERSIONS = ".versions"


def _logged(action: str, **fields) -> dict | None:
    """An entry in 4CE's audit trail - append-only, hash-chained - when the
    backend keeps one. Recording never fails the tool."""
    try:
        from open_webui.utils.fource_audit import record
    except Exception:
        return None
    return record(action, **fields)


def _default_workspace() -> Path:
    try:
        from open_webui.env import DATA_DIR

        return Path(DATA_DIR) / "4ce" / "workspace"
    except Exception:
        return Path("data") / "4ce" / "workspace"


def _inside(root: Path, requested: str) -> Path | None:
    """The file a relative path names inside `root`, or None when the path
    would leave it. Absolute paths, drive letters and "..", and links that
    point elsewhere, are all refused: resolving first catches every one."""
    raw = str(requested or "").strip().replace("\\", "/").strip()
    if not raw or "\x00" in raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw) or raw.startswith("~"):
        return None
    base = root.resolve()
    target = (base / raw).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None
    return target if target != base else None


def _kb(size: int) -> str:
    return f"{max(1, round(size / 1024))} KB"


class Tools:
    class Valves(BaseModel):
        workspace: str = Field(
            default="",
            description="The one folder 4CE may write, and read. Blank uses DATA_DIR/4ce/workspace.",
        )
        read_only: str = Field(
            default="",
            description="Further folders 4CE may read but never write - an SOP share, say. Separate them with ;",
        )
        max_read_kb: int = Field(default=512, description="Largest file read into a conversation.")
        max_write_kb: int = Field(default=2048, description="Largest file 4CE will write.")

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    # -- where ----------------------------------------------------------------

    def _workspace(self) -> Path:
        root = Path(self.valves.workspace).expanduser() if self.valves.workspace.strip() else _default_workspace()
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _roots(self) -> list[tuple[str, Path]]:
        """Where a read may look: the workspace, then each read-only folder."""
        roots = [("workspace", self._workspace())]
        for n, folder in enumerate(p.strip() for p in self.valves.read_only.split(";") if p.strip()):
            path = Path(folder).expanduser()
            if path.is_dir():
                roots.append((f"read-only folder {n + 1}", path))
        return roots

    # -- tools ----------------------------------------------------------------

    async def list_files(self, folder: str = "") -> str:
        """
        List the files in 4CE's workspace, or in one folder of it.

        :param folder: A folder inside the workspace, relative to it. Blank lists the whole workspace.
        :return: The files, with their sizes, or why they could not be listed.
        """
        lines: list[str] = []
        for label, root in self._roots():
            base = _inside(root, folder) if folder.strip() else root.resolve()
            if base is None or not base.is_dir():
                continue
            found = sorted(
                p for p in base.rglob("*")
                if p.is_file() and VERSIONS not in p.relative_to(root.resolve()).parts
            )[:200]
            lines.append(f"**{label}** - {len(found)} file{'s' if len(found) != 1 else ''}")
            lines += [f"- `{p.relative_to(root.resolve()).as_posix()}` ({_kb(p.stat().st_size)})" for p in found]
        _logged("file.list", tool="list_files", folder=folder or None)
        return "\n".join(lines) if lines else f"`{folder}` is not a folder 4CE can read."

    async def read_file(self, path: str) -> str:
        """
        Read a text file from 4CE's workspace, or from a read-only folder it has been given.

        :param path: The file, relative to the workspace, e.g. notes/p101b.md.
        :return: The file's text, or why it could not be read.
        """
        for label, root in self._roots():
            target = _inside(root, path)
            if target is None:
                return f"`{path}` is outside the folders 4CE may read, so it was not read."
            if not target.is_file():
                continue
            size = target.stat().st_size
            if size > self.valves.max_read_kb * 1024:
                return f"`{path}` is {_kb(size)}, over the {self.valves.max_read_kb} KB 4CE reads into a conversation."
            data = await asyncio.to_thread(target.read_bytes)
            if b"\x00" in data[:4096]:
                return f"`{path}` is not a text file. A spreadsheet is read with read_sheet."
            entry = _logged("file.read", tool="read_file", file=path, root=label,
                            sha256=hashlib.sha256(data).hexdigest(), bytes=size)
            text = data.decode("utf-8", errors="replace")
            fence = "````" if "```" in text else "```"
            return (
                f"`{path}` - {_kb(size)}, from the {label}"
                + (f", audit trail entry {entry['seq']}" if entry else "")
                + f":\n\n{fence}\n{text}\n{fence}"
            )
        return f"`{path}` is not in the workspace."

    async def write_file(self, path: str, content: str) -> str:
        """
        Write a text file into 4CE's workspace. Overwriting keeps the earlier version.

        Use this when the request asks for something to be saved or filed, e.g. notes, a CSV
        of readings, or a script. Writes only inside the workspace, and only text types.

        :param path: Where, relative to the workspace, with the extension, e.g. notes/p101b.md.
        :param content: The exact text to write.
        :return: Where it was written and what was kept, or why it was not written.
        """
        root = self._workspace()
        target = _inside(root, path)
        if target is None:
            return f"`{path}` is outside the workspace, so nothing was written."
        relative = target.relative_to(root.resolve())
        if VERSIONS in relative.parts:
            return "The earlier versions of files are kept, not rewritten; nothing was written."
        if target.suffix.lower() not in WRITABLE:
            return (
                f"`{target.name}` is not a type 4CE writes into the workspace. "
                "It writes: " + ", ".join(sorted(WRITABLE)) + "."
            )
        payload = str(content or "").encode("utf-8")
        if not payload.strip():
            return "The content is empty; nothing was written."
        if len(payload) > self.valves.max_write_kb * 1024:
            return f"That is {_kb(len(payload))}, over the {self.valves.max_write_kb} KB limit; nothing was written."

        kept = replaced = None
        if target.exists():
            previous = await asyncio.to_thread(target.read_bytes)
            if previous == payload:
                return f"`{relative.as_posix()}` already holds exactly this; nothing was written."
            # Every earlier version is kept beside the workspace's own files.
            history = root.resolve() / VERSIONS / relative
            history.mkdir(parents=True, exist_ok=True)
            number = len(list(history.glob(f"{target.stem}.v*{target.suffix}"))) + 1
            kept = history / f"{target.stem}.v{number}{target.suffix}"
            await asyncio.to_thread(kept.write_bytes, previous)
            replaced = hashlib.sha256(previous).hexdigest()
        target.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, payload)

        entry = _logged(
            "file.write", tool="write_file", file=relative.as_posix(),
            sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload),
            replaced=replaced, kept=kept.relative_to(root.resolve()).as_posix() if kept else None,
        )
        return (
            f"**Written** `{relative.as_posix()}` in the workspace · {_kb(len(payload))}"
            + (f" · the earlier version kept as `{kept.relative_to(root.resolve()).as_posix()}`" if kept else "")
            + (f" · audit trail entry {entry['seq']}" if entry else "")
        )
