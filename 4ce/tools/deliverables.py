"""
title: 4CE Deliverables
author: 4CE
version: 0.1.0
description: Produces real office documents from agent output - approval notes, inspection summaries and reports as .docx files registered for download. Generated entirely on the local machine.
"""

import asyncio
import io
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from open_webui.models.files import FileForm, Files
from open_webui.storage.provider import Storage


# Text types 4CE will write. Deliberately a list rather than "anything the model
# named": a file a reviewer downloads from an approval workflow should not be an
# executable or an installer.
ARTIFACT_TYPES = {
    ".py": "text/x-python",
    ".sql": "application/sql",
    ".js": "text/javascript",
    ".ts": "text/plain",
    ".java": "text/x-java-source",
    ".c": "text/x-c",
    ".cpp": "text/x-c",
    ".cs": "text/plain",
    ".go": "text/plain",
    ".rs": "text/plain",
    ".rb": "text/plain",
    ".sh": "text/x-shellscript",
    ".ps1": "text/plain",
    ".r": "text/plain",
    ".m": "text/plain",
    ".csv": "text/csv",
    ".tsv": "text/tab-separated-values",
    ".json": "application/json",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
    ".xml": "application/xml",
    ".html": "text/html",
    ".css": "text/css",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".ini": "text/plain",
    ".toml": "text/plain",
    ".env": "text/plain",
    ".log": "text/plain",
}


def _safe_filename(filename: str) -> str | None:
    """A flat, sanitised name whose extension 4CE is willing to write."""
    name = Path(str(filename).strip().replace("\\", "/")).name
    stem, dot, suffix = name.rpartition(".")
    if not dot or f".{suffix.lower()}" not in ARTIFACT_TYPES:
        return None
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)[:60].strip("._-") or "artifact"
    return f"{stem}.{suffix.lower()}"


class Tools:
    class Valves(BaseModel):
        organisation: str = Field(
            default="",
            description="Organisation name printed in the document header. Leave blank to omit.",
        )
        prepared_by: str = Field(
            default="4CE Sovereign AI Workbench",
            description="Value used for the 'Prepared by' field.",
        )
        classification: str = Field(
            default="INTERNAL — CONFIDENTIAL",
            description="Classification banner printed on every document. Leave blank to omit.",
        )
        output_dir: str = Field(
            default="",
            description=(
                "Directory on this machine where finished documents are also written, for "
                "example an inspection share. Blank keeps them as downloads only."
            ),
        )

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    async def create_word_document(
        self,
        title: str,
        body: str,
        reference: str = "",
        __user__: dict | None = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Create a formatted Word (.docx) document from the supplied content and return a download link.

        Use this whenever the user asks for an approval note, inspection summary, report or any
        deliverable that should be a real Word file rather than a chat reply.

        :param title: Document title, e.g. "Approval Note - Heat Exchanger E-101 Inspection".
        :param body: The document content. Markdown-style '## ' headings, '- ' bullets and blank-line separated paragraphs are honoured.
        :param reference: Optional reference or file number printed in the document header.
        :return: A markdown download link to the generated document, or an error description.
        """
        if not title.strip():
            return "A document title is required."
        if not body.strip():
            return "The document body is empty; nothing was generated."
        if not __user__ or not __user__.get("id"):
            return "The document could not be attributed to a user, so it was not generated."

        await _emit(__event_emitter__, "deliverable", f"JARVIS: writing '{title}' as a Word document")

        try:
            payload = await asyncio.to_thread(self._build_docx, title, body, reference)
        except ImportError:
            return (
                "The `python-docx` package is not available in this backend, so the document "
                "could not be generated."
            )
        except Exception as exc:
            return f"The document could not be generated: {exc}"

        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", title.strip())[:60].strip("_") or "document"
        filename = f"{safe}.docx"
        file_id = str(uuid.uuid4())

        try:
            contents, path = await asyncio.to_thread(
                Storage.upload_file, io.BytesIO(payload), f"{file_id}_{filename}", {}
            )
            record = await Files.insert_new_file(
                __user__["id"],
                FileForm(
                    id=file_id,
                    filename=filename,
                    path=path,
                    data={},
                    meta={
                        "name": filename,
                        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "size": len(contents),
                    },
                ),
            )
        except Exception as exc:
            return f"The document was generated but could not be stored: {exc}"

        if record is None:
            return "The document was generated but could not be registered for download."

        # The document is registered for download either way; a configured directory
        # is an additional copy on disk, for a share the plant already uses.
        saved = ""
        keep = (self.valves.output_dir or "").strip()
        if keep:
            try:
                destination = Path(keep).expanduser().resolve()
                await asyncio.to_thread(destination.mkdir, parents=True, exist_ok=True)
                target = destination / filename
                await asyncio.to_thread(target.write_bytes, payload)
                saved = f"\n\nAlso written to `{target}`."
            except Exception as exc:
                saved = f"\n\nIt could not be written to `{keep}`: {exc}"

        await _emit(__event_emitter__, "deliverable", "Document ready", done=True)
        return (
            f"Generated **{filename}** ({len(payload) // 1024 or 1} KB), stored locally.\n\n"
            f"[Download {filename}](/api/v1/files/{file_id}/content)"
            + saved
        )

    async def save_artifact(
        self,
        filename: str,
        content: str,
        __user__: dict | None = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Save text content as a named file of any ordinary text type and return a download link.

        Use this when the request asks for a file rather than a document: source code as
        .py or .sql, data as .csv or .json, notes as .md. For a formal report or an
        approval note, use create_word_document instead.

        :param filename: The file name including its extension, for example readings.csv or median.py.
        :param content: The exact text to write. It is written verbatim.
        :return: A confirmation with a download link, or the reason it could not be saved.
        """
        if not filename or not filename.strip():
            return "A file name is required."
        if not content or not content.strip():
            return "The file is empty; nothing was saved."
        if not __user__ or not __user__.get("id"):
            return "The file could not be attributed to a user, so it was not saved."

        safe = _safe_filename(filename)
        if safe is None:
            return (
                f"`{filename}` is not a text file type 4CE will write. Allowed types: "
                + ", ".join(sorted(ARTIFACT_TYPES)) + "."
            )

        await _emit(__event_emitter__, "artifact", f"JARVIS: saving {safe}")
        payload = content.encode("utf-8")
        file_id = str(uuid.uuid4())
        media = ARTIFACT_TYPES[Path(safe).suffix.lower()]

        try:
            contents, path = await asyncio.to_thread(
                Storage.upload_file, io.BytesIO(payload), f"{file_id}_{safe}", {}
            )
            record = await Files.insert_new_file(
                __user__["id"],
                FileForm(
                    id=file_id,
                    filename=safe,
                    path=path,
                    data={},
                    meta={"name": safe, "content_type": media, "size": len(contents)},
                ),
            )
        except Exception as exc:
            return f"The file was prepared but could not be stored: {exc}"
        if record is None:
            return "The file was prepared but could not be registered for download."

        saved = ""
        keep = (self.valves.output_dir or "").strip()
        if keep:
            try:
                destination = Path(keep).expanduser().resolve()
                await asyncio.to_thread(destination.mkdir, parents=True, exist_ok=True)
                target = destination / safe
                await asyncio.to_thread(target.write_bytes, payload)
                saved = f" Also written to `{target}`."
            except Exception as exc:
                saved = f" It could not be written to `{keep}`: {exc}"

        await _emit(__event_emitter__, "artifact", f"{safe} ready", done=True)
        return (
            f"Saved **{safe}** ({len(payload) // 1024 or 1} KB)."
            f" [Download {safe}](/api/v1/files/{file_id}/content){saved}"
        )

    def _build_docx(self, title: str, body: str, reference: str) -> bytes:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Pt

        document = Document()

        if self.valves.classification.strip():
            banner = document.add_paragraph(self.valves.classification.strip())
            banner.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = banner.runs[0]
            run.bold = True
            run.font.size = Pt(9)

        if self.valves.organisation.strip():
            org = document.add_paragraph(self.valves.organisation.strip())
            org.alignment = WD_ALIGN_PARAGRAPH.CENTER
            org.runs[0].font.size = Pt(11)

        document.add_heading(title.strip(), level=0)

        meta = document.add_table(rows=0, cols=2)
        meta.style = "Table Grid"
        for label, value in (
            ("Reference", reference.strip() or "—"),
            ("Date", datetime.now().strftime("%d %B %Y")),
            ("Prepared by", self.valves.prepared_by.strip() or "—"),
        ):
            row = meta.add_row().cells
            row[0].text = label
            row[1].text = value
            row[0].paragraphs[0].runs[0].bold = True

        document.add_paragraph()
        _render_body(document, body)

        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue()


def _render_body(document: Any, body: str) -> None:
    for block in body.replace("\r\n", "\n").split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        if all(line.strip().startswith(("- ", "* ")) for line in lines if line.strip()):
            for line in lines:
                text = line.strip()[2:].strip()
                if text:
                    document.add_paragraph(_strip_marks(text), style="List Bullet")
            continue
        if re.match(r"^\d+[.)]\s", lines[0].strip()) and len(lines) > 1:
            for line in lines:
                text = re.sub(r"^\d+[.)]\s*", "", line.strip())
                if text:
                    document.add_paragraph(_strip_marks(text), style="List Number")
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", lines[0].strip())
        if heading:
            document.add_heading(_strip_marks(heading.group(2)), level=min(len(heading.group(1)), 4))
            rest = "\n".join(lines[1:]).strip()
            if rest:
                document.add_paragraph(_strip_marks(rest))
            continue
        document.add_paragraph(_strip_marks(block.replace("\n", " ")))


def _strip_marks(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text.strip()


async def _emit(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})
