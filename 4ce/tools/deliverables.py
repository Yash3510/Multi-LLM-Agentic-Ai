"""
title: 4CE Deliverables
author: 4CE
version: 0.1.0
description: Produces real office files from agent output - approval notes and reports as .docx, tables as .xlsx workbooks, decks as .pptx - registered for download. Generated entirely on the local machine.
"""

import asyncio
import hashlib
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


def _logged(action: str, **fields) -> None:
    """An entry in 4CE's audit trail - append-only, hash-chained - when the
    backend keeps one. Recording never fails the tool."""
    try:
        from open_webui.utils.fource_audit import record
    except Exception:
        return
    record(action, **fields)


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
        document_type: str = "Report",
        __user__: dict | None = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
        __signoff__: dict | None = None,
        __record__: list | None = None,
        __sources__: list | None = None,
        __revision__: dict | None = None,
        __checks__: list | None = None,
        __passages__: list | None = None,
        __cited__: list | None = None,
    ) -> str:
        """
        Create a formatted Word (.docx) document from the supplied content and return a download link.

        Use this whenever the user asks for an approval note, inspection summary, report or any
        deliverable that should be a real Word file rather than a chat reply.

        :param title: Document title, e.g. "Approval Note - Heat Exchanger E-101 Inspection".
        :param body: The document content, in markdown: headings, paragraphs, bold and italic, bullet and numbered lists, tables, quotes and code blocks are all laid out.
        :param reference: Optional reference or file number. One is generated when left blank.
        :param document_type: What the document is, printed above the title, e.g. "Approval note" or "Inspection summary".
        :return: A markdown download link to the generated document, or an error description.
        """
        # __signoff__ and __record__ are the approval and the verification
        # record. Parameters that start with "__" are left out of the tool spec
        # the model sees, so only the orchestrator - which actually ran the
        # approval gate - can state that a person approved this document.
        if not title.strip():
            return "A document title is required."
        if not body.strip():
            return "The document body is empty; nothing was generated."
        if not __user__ or not __user__.get("id"):
            return "The document could not be attributed to a user, so it was not generated."

        await _emit(__event_emitter__, "deliverable", f"JARVIS: writing '{title}' as a Word document")

        images = await _load_images(body)
        try:
            payload = await asyncio.to_thread(
                self._build_docx, title, body, reference, document_type, __signoff__, __record__,
                __sources__, __revision__, __checks__, __passages__, __cited__, images,
            )
        except ImportError:
            return (
                "The `python-docx` package is not available in this backend, so the document "
                "could not be generated."
            )
        except Exception as exc:
            return f"The document could not be generated: {exc}"

        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", title.strip())[:60].strip("_") or "document"
        # Dated, so a second report on the same subject does not look like the first.
        filename = f"{safe}_{datetime.now():%Y-%m-%d}.docx"
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
        _logged("file.write", tool="create_word_document", file=filename, id=file_id,
                sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))

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
            # One readable line: what it is, its size, where it lives, and the
            # link. The file name alone ran two lines, underlined, and said
            # less than the title does.
            f"**Word report** · {title.strip()} · {len(payload) // 1024 or 1} KB, stored on this "
            f"machine · [Download .docx](/api/v1/files/{file_id}/content)"
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
        _logged("file.write", tool="save_artifact", file=safe, id=file_id,
                sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))

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
            f"**{safe}** · {len(payload) // 1024 or 1} KB, stored on this machine · "
            f"[Download](/api/v1/files/{file_id}/content){saved}"
        )

    async def create_spreadsheet(
        self,
        title: str,
        body: str,
        __user__: dict | None = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
        __record__: list | None = None,
        __sources__: list | None = None,
        __calculations__: list | None = None,
    ) -> str:
        """
        Create an Excel (.xlsx) workbook from the tables in the supplied content and return a download link.

        Use this when the request asks for a spreadsheet, an Excel file or a workbook.

        :param title: Workbook title, e.g. "P-101B readings".
        :param body: The content, in markdown. Every table becomes a sheet of its own: numbers are stored as numbers, a unit shared by a whole column moves into its header, and a stated total that adds up becomes a live SUM formula.
        :return: A markdown download link to the workbook, or the reason it could not be made.
        """
        refused = _refusal(title, body, __user__)
        if refused:
            return refused
        await _emit(__event_emitter__, "deliverable", f"JARVIS: writing '{title}' as an Excel workbook")
        try:
            payload = await asyncio.to_thread(
                _build_xlsx, title, body, __record__ or [], __sources__ or [], __calculations__ or []
            )
        except ImportError:
            return "The `openpyxl` package is not available in this backend, so the workbook could not be made."
        except Exception as exc:
            return f"The workbook could not be made: {exc}"
        return await self._store(
            __user__, __event_emitter__, title, payload, "xlsx", "Excel workbook",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    async def create_presentation(
        self,
        title: str,
        body: str,
        document_type: str = "Deliverable",
        __user__: dict | None = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
        __record__: list | None = None,
        __sources__: list | None = None,
    ) -> str:
        """
        Create a PowerPoint (.pptx) deck from the supplied content and return a download link.

        Use this when the request asks for slides, a deck, a presentation or a PowerPoint file.

        :param title: Deck title, e.g. "P-101B seal replacement - for approval".
        :param body: The content, in markdown. The opening paragraph becomes the key-message slide, every ### section a slide of bullets, every table a table slide; the full text of each section goes into the speaker notes.
        :param document_type: What the deck is, shown above the title, e.g. "Board update".
        :return: A markdown download link to the deck, or the reason it could not be made.
        """
        refused = _refusal(title, body, __user__)
        if refused:
            return refused
        await _emit(__event_emitter__, "deliverable", f"JARVIS: writing '{title}' as a PowerPoint deck")
        images = await _load_images(body)
        try:
            payload = await asyncio.to_thread(
                _build_pptx, title, body, document_type, __record__ or [], __sources__ or [], images
            )
        except ImportError:
            return "The `python-pptx` package is not available in this backend, so the deck could not be made."
        except Exception as exc:
            return f"The deck could not be made: {exc}"
        return await self._store(
            __user__, __event_emitter__, title, payload, "pptx", "PowerPoint deck",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    async def _store(self, user: dict, emitter, title: str, payload: bytes, suffix: str,
                     kind: str, media: str) -> str:
        """Register a built file for download - and copy it to output_dir when one is set -
        and answer in the one-line shape the chat draws as a file card."""
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", title.strip())[:60].strip("_") or "deliverable"
        filename = f"{safe}_{datetime.now():%Y-%m-%d}.{suffix}"
        file_id = str(uuid.uuid4())
        try:
            contents, path = await asyncio.to_thread(
                Storage.upload_file, io.BytesIO(payload), f"{file_id}_{filename}", {}
            )
            record = await Files.insert_new_file(
                user["id"],
                FileForm(
                    id=file_id, filename=filename, path=path, data={},
                    meta={"name": filename, "content_type": media, "size": len(contents)},
                ),
            )
        except Exception as exc:
            return f"The {kind.lower()} was made but could not be stored: {exc}"
        if record is None:
            return f"The {kind.lower()} was made but could not be registered for download."
        _logged("file.write", tool=kind, file=filename, id=file_id,
                sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))

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

        await _emit(emitter, "deliverable", f"{kind} ready", done=True)
        return (
            f"**{kind}** · {title.strip()} · {len(payload) // 1024 or 1} KB, stored on this "
            f"machine · [Download .{suffix}](/api/v1/files/{file_id}/content)" + saved
        )

    def _build_docx(
        self,
        title: str,
        body: str,
        reference: str,
        document_type: str = "",
        signoff: dict | None = None,
        record: list | None = None,
        sources: list | None = None,
        revision: dict | None = None,
        checks: list | None = None,
        passages: list | None = None,
        cited: list | None = None,
        images: dict | None = None,
    ) -> bytes:
        return _Report(
            self.valves, title, body, reference, document_type, signoff or {}, record or [], sources,
            revision, checks, passages, cited, images,
        ).build()


# ---------------------------------------------------------------------------
# The 4CE report
#
# House style, taken from the 4CE vendor site: indigo labels, ink headings,
# warm paper panels and a single deep-orange accent. A .docx can only use the
# fonts installed on the reader's machine, and Office's own fonts are not on a
# Mac without Office: Calibri and Consolas fell back to Times in Pages and
# Quick Look. So only fonts every Mac and Windows machine has: Arial for Inter
# (text, headings and the wordmark) and Courier New for JetBrains Mono. A4,
# because that is what Indian plants print on.
#
# Layout that survives simple readers: Quick Look and TextEdit ignore table
# widths, cell padding and paragraph shading. So spacing inside cells comes
# from paragraph indents and spacing, which every reader honours, and quotes
# and code sit in shaded one-cell tables - cell shading is also universal.
# ---------------------------------------------------------------------------

INK = "1E1B33"  # headings and values
BODY = "2E2B3A"  # running text
MUTED = "5F5B6B"
LABEL = "706B5E"  # small-caps labels: 4.9:1 on white, 4.5:1 on the paper panel
INDIGO = "3C3C8E"
ACCENT = "C2410C"
GOOD = "1F7A4D"  # a check that held
PAPER = "F6F4EE"  # panels
FILL = "F4F2EC"  # table header row
RULE = "E8E3D7"  # table hairlines
LINE = "D9D3C6"  # rules between sections: a shade darker, so they survive on screen
SANS = "Arial"
# Headings, the title and the wordmark are in the sans face too. Georgia set
# them before, and its old-style figures drop below the line: the wordmark
# read "4CE" with a sunken 4, and "SOP-MEC-014" in a title read as "o14".
HEAD = SANS
MONO = "Courier New"

PAGE_W, PAGE_H, MARGIN = 21.0, 29.7, 2.2  # cm
TEXT_W = PAGE_W - 2 * MARGIN  # 16.6 cm


def _logo_png() -> bytes | None:
    """The bare 4CE mark, drawn from the vector trace by make_assets.py.

    The backend empties its static directory on every start and refills it
    from the frontend build, so the build is the second place to look.
    """
    try:
        from open_webui.env import FRONTEND_BUILD_DIR, STATIC_DIR
    except Exception:
        return None
    for folder in (Path(STATIC_DIR), Path(FRONTEND_BUILD_DIR) / "static"):
        try:
            return (folder / "logo-mark.png").read_bytes()
        except OSError:
            continue
    return None


def _solid_png(hex_colour: str, width: int, height: int) -> bytes:
    """A flat colour bar as a tiny PNG - Word has no simple short rule."""
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), "#" + hex_colour).save(buffer, format="PNG")
    return buffer.getvalue()


# Child order for the property elements this module writes, from the Office
# Open XML schema (ECMA-376 part 1). Word refuses a file whose properties are
# out of order - a paragraph border after its spacing, say - and python-docx
# only knows the order for the properties it manages itself.
_ORDER = {
    "pPr": (
        "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
        "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
        "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
        "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing",
        "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
        "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange",
    ),
    "rPr": (
        "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
        "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish",
        "webHidden", "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight",
        "u", "effect", "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang",
        "eastAsianLayout", "specVanish", "oMath",
    ),
    "tblPr": (
        "tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
        "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd",
        "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription",
    ),
    "tcPr": (
        "cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap",
        "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark",
    ),
}


def _put(parent: Any, child: Any) -> Any:
    """Insert a property element in schema order, replacing any old one."""
    for old in parent.findall(child.tag):
        parent.remove(old)
    local = lambda element: element.tag.rsplit("}", 1)[-1]
    order = _ORDER.get(local(parent))
    if order and local(child) in order:
        rank = order.index(local(child))
        for index, existing in enumerate(parent):
            name = local(existing)
            if name in order and order.index(name) > rank:
                parent.insert(index, child)
                return child
    parent.append(child)
    return child


def _el(tag: str, **attrs: str) -> Any:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    element = OxmlElement(tag)
    for key, value in attrs.items():
        element.set(qn(f"w:{key}"), str(value))
    return element


def _fonts(rpr: Any, name: str) -> None:
    """Set a font on every script slot and drop theme fonts, which override it."""
    from docx.oxml.ns import qn

    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = _put(rpr, _el("w:rFonts"))
    for slot in ("ascii", "hAnsi", "cs", "eastAsia"):
        rfonts.set(qn(f"w:{slot}"), name)
    for slot in ("asciiTheme", "hAnsiTheme", "cstheme", "eastAsiaTheme"):
        rfonts.attrib.pop(qn(f"w:{slot}"), None)


def _tracking(run: Any, points: float) -> None:
    _put(run._r.get_or_add_rPr(), _el("w:spacing", val=round(points * 20)))


def _border(paragraph: Any, side: str, colour: str, eighths: int, space: int = 1) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    from docx.oxml.ns import qn

    borders = ppr.find(qn("w:pBdr"))
    if borders is None:
        borders = _put(ppr, _el("w:pBdr"))
    borders.append(_el(f"w:{side}", val="single", sz=eighths, space=space, color=colour))


def _shade_paragraph(paragraph: Any, colour: str) -> None:
    _put(paragraph._p.get_or_add_pPr(), _el("w:shd", val="clear", color="auto", fill=colour))


def _shade_cell(cell: Any, colour: str) -> None:
    _put(cell._tc.get_or_add_tcPr(), _el("w:shd", val="clear", color="auto", fill=colour))


def _frame(table: Any, colour: str = RULE, outer: tuple = (), inside_h: bool = False) -> None:
    """Table borders: only the edges named, as hairlines; everything else off."""
    borders = _el("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        on = edge in outer or (edge == "insideH" and inside_h)
        attrs = {"val": "single", "sz": 4, "space": 0, "color": colour} if on else {"val": "nil"}
        borders.append(_el(f"w:{edge}", **attrs))
    _put(table._tbl.tblPr, borders)


def _padding(table: Any, top: float, side: float, bottom: float | None = None) -> None:
    """Cell padding for the whole table, in points."""
    margins = _el("w:tblCellMar")
    for edge, value in (("top", top), ("left", side), ("bottom", top if bottom is None else bottom), ("right", side)):
        margins.append(_el(f"w:{edge}", w=round(value * 20), type="dxa"))
    _put(table._tbl.tblPr, margins)


def _columns(table: Any, widths_cm: list[float]) -> None:
    """Fixed column widths, on the grid and on every cell (Word reads both)."""
    from docx.shared import Cm

    table.autofit = False
    _put(table._tbl.tblPr, _el("w:tblW", w=round(sum(widths_cm) / 2.54 * 1440), type="dxa"))
    _put(table._tbl.tblPr, _el("w:tblLayout", type="fixed"))
    for index, width in enumerate(widths_cm):
        table.columns[index].width = Cm(width)
        for cell in table.columns[index].cells:
            cell.width = Cm(width)


def _field(paragraph: Any, instruction: str, **style: Any) -> None:
    """A Word field (PAGE, NUMPAGES), shown as 1 until Word lays out pages."""
    run = _run(paragraph, "", **style)
    run._r.append(_el("w:fldChar", fldCharType="begin"))
    code = _el("w:instrText")
    code.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    code.text = f" {instruction} "
    run._r.append(code)
    run._r.append(_el("w:fldChar", fldCharType="separate"))
    shown = _el("w:t")
    shown.text = "1"
    run._r.append(shown)
    run._r.append(_el("w:fldChar", fldCharType="end"))


def _run(
    paragraph: Any,
    text: str,
    *,
    font: str | None = None,
    size: float | None = None,
    colour: str | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    caps: bool = False,
    track: float | None = None,
    underline: bool = False,
    fill: str | None = None,
    sup: bool = False,
) -> Any:
    from docx.shared import Pt, RGBColor

    run = paragraph.add_run(text)
    if font:
        _fonts(run._r.get_or_add_rPr(), font)
    if size:
        run.font.size = Pt(size)
    if colour:
        run.font.color.rgb = RGBColor.from_string(colour)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if caps:
        run.font.all_caps = True
    if underline:
        run.underline = True
    if track:
        _tracking(run, track)
    if fill:
        _put(run._r.get_or_add_rPr(), _el("w:shd", val="clear", color="auto", fill=fill))
    if sup:
        run.font.superscript = True
    return run


def _pad(paragraph: Any, side_cm: float = 0.2, before: float = 3, after: float = 3, line: float = 1.15) -> None:
    """Padding for text in a table cell, as paragraph indent and spacing."""
    from docx.shared import Cm

    paragraph.paragraph_format.left_indent = Cm(side_cm)
    paragraph.paragraph_format.right_indent = Cm(side_cm)
    _spacing(paragraph, before, after, line)


def _spacing(paragraph: Any, before: float = 0, after: float = 0, line: float | None = None) -> None:
    from docx.shared import Pt

    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    if line:
        fmt.line_spacing = line


# Markdown, as the agents write it. Line-based on purpose: the model output is
# not always well-formed, and a line that matches nothing is simply text.
_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
_RULE_LINE = re.compile(r"^\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,}|[—–])\s*$")
_QUOTE = re.compile(r"^\s{0,3}>\s?(.*)$")
_ITEM = re.compile(r"^(\s*)([-*+•]|\d{1,3}[.)])\s+(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_LABEL_ONLY = re.compile(r"^\*\*([^*]{1,80}?)\*\*:?$")
# An image the answer shows from this machine's file store - the orchestrator's
# annotated copy of a scan, with each field it read boxed and numbered.
_IMAGE_LINE = re.compile(r"^\s*!\[([^\]]*)\]\(/api/v1/files/([0-9a-fA-F-]{36})/content\)\s*$", re.M)
_INLINE = re.compile(
    r"\*\*\*(?=\S)(?P<bi>.+?)(?<=\S)\*\*\*"
    r"|\*\*(?=\S)(?P<b>.+?)(?<=\S)\*\*"
    r"|__(?=\S)(?P<b2>.+?)(?<=\S)__"
    r"|(?<![\w*])\*(?=\S)(?P<i>.+?)(?<=\S)\*(?![\w*])"
    r"|(?<!\w)_(?=\S)(?P<i2>.+?)(?<=\S)_(?!\w)"
    r"|`(?P<code>[^`]+)`"
    r"|\s*\[(?P<cite>\d+(?:\s*,\s*\d+)*)\](?!\()"
    r"|\[(?P<link>[^\]]+)\]\((?P<url>[^)\s]+)\)"
)


class _Report:
    def __init__(
        self,
        valves: Any,
        title: str,
        body: str,
        reference: str,
        document_type: str,
        signoff: dict,
        record: list,
        sources: list | None = None,
        revision: dict | None = None,
        checks: list | None = None,
        passages: list | None = None,
        cited: list | None = None,
        images: dict | None = None,
    ):
        self.valves = valves
        self.images = images or {}
        self.checks = [c for c in (checks or []) if isinstance(c, dict) and str(c.get("text", "")).strip()]
        self.passages = [str(p or "") for p in (passages or [])]
        # Which sources the text cites (1-based); None when not told.
        self.cited = {int(n) for n in cited} if cited is not None else None
        self.sources = [str(name) for name in (sources or []) if str(name).strip()]
        self.revision = revision if revision and revision.get("objections") else None
        self.title = title.strip()
        self.body = body
        self.issued = datetime.now().astimezone()
        self.reference = (reference or "").strip() or (
            f"4CE-{self.issued:%Y%m%d}-{uuid.uuid4().hex[:4].upper()}"
        )
        self.kind = (document_type or "").strip() or "Report"
        self.signoff = signoff
        self.record = [(str(k), str(v)) for k, v in record if str(v).strip()]
        self.logo = _logo_png()
        self.lists = 0

    # -- document ----------------------------------------------------------

    def build(self) -> bytes:
        from docx import Document

        self.doc = Document()
        zoom = self.doc.settings.element.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}zoom"
        )
        if zoom is not None:
            # The default template's <w:zoom> lacks the percent the schema requires.
            zoom.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}percent", "100")
        self._page()
        self._styles()
        self._header_footer()
        self._masthead()
        self._markdown(self.body)
        if self.revision:
            self._revisions()
        if self.checks:
            self._checks()
        if self.sources:
            self._sources()
        if self.record:
            self._record()
        if self.signoff.get("approved_by"):
            self._signoff()
        self._properties()
        buffer = io.BytesIO()
        self.doc.save(buffer)
        return buffer.getvalue()

    def _page(self) -> None:
        from docx.shared import Cm

        section = self.doc.sections[0]
        section.page_width, section.page_height = Cm(PAGE_W), Cm(PAGE_H)
        section.left_margin = section.right_margin = Cm(MARGIN)
        section.top_margin, section.bottom_margin = Cm(2.3), Cm(2.1)
        section.header_distance, section.footer_distance = Cm(1.05), Cm(0.95)
        # The first page carries the full masthead, so its header stays empty.
        section.different_first_page_header_footer = True

    def _styles(self) -> None:
        from docx.enum.style import WD_STYLE_TYPE
        from docx.shared import Cm, Pt, RGBColor

        styles = self.doc.styles

        normal = styles["Normal"]
        _fonts(normal.element.get_or_add_rPr(), SANS)
        normal.font.size = Pt(10.5)
        normal.font.color.rgb = RGBColor.from_string(BODY)
        _spacing_style(normal, 0, 7, 1.22)

        for name, font, size, colour, bold, before, after in (
            ("Heading 1", HEAD, 15, INK, True, 20, 6),
            ("Heading 2", HEAD, 12.5, INK, True, 16, 5),
            ("Heading 3", SANS, 11, INK, True, 12, 3),
            ("Heading 4", SANS, 10.5, MUTED, True, 10, 2),
        ):
            style = styles[name]
            _fonts(style.element.get_or_add_rPr(), font)
            style.font.size = Pt(size)
            style.font.bold = bold
            style.font.italic = False
            style.font.color.rgb = RGBColor.from_string(colour)
            _spacing_style(style, before, after, 1.1)
            style.paragraph_format.keep_with_next = True

        for name in ("List Bullet", "List Bullet 2", "List Bullet 3", "List Number", "List Number 2", "List Number 3"):
            _spacing_style(styles[name], 0, 3, 1.22)

        quote = styles.add_style("4CE Quote", WD_STYLE_TYPE.PARAGRAPH)
        quote.base_style = normal
        quote.font.italic = True
        quote.font.color.rgb = RGBColor.from_string(BODY)
        quote.paragraph_format.left_indent = Cm(0.35)
        quote.paragraph_format.right_indent = Cm(0.2)
        _spacing_style(quote, 2, 2, 1.25)

        code = styles.add_style("4CE Code", WD_STYLE_TYPE.PARAGRAPH)
        code.base_style = normal
        _fonts(code.element.get_or_add_rPr(), MONO)
        code.font.size = Pt(9)
        code.font.color.rgb = RGBColor.from_string(INK)
        code.paragraph_format.left_indent = Cm(0.25)
        code.paragraph_format.right_indent = Cm(0.25)
        _spacing_style(code, 0, 0, 1.15)

    def _header_footer(self) -> None:
        from docx.enum.text import WD_TAB_ALIGNMENT
        from docx.shared import Cm

        section = self.doc.sections[0]
        classification = (self.valves.classification or "").strip()

        # Pages 2+: the mark, the name, the document, and its classification.
        head = section.header.paragraphs[0]
        head.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
        if self.logo:
            head.add_run().add_picture(io.BytesIO(self.logo), height=Cm(0.42))
            _run(head, "  ")
        _run(head, "4CE", font=HEAD, size=9.5, colour=INK, bold=True, track=-0.1)
        short = self.title if len(self.title) <= 64 else self.title[:61].rstrip() + "…"
        _run(head, f"   ·   {short}", size=8.5, colour=MUTED)
        if classification:
            _run(head, "\t" + classification, size=7, colour=INDIGO, bold=True, caps=True, track=1.2)
        _border(head, "bottom", RULE, 4, 6)

        # Every page, the first included: where it came from, and page x of y.
        for footer in (section.footer, section.first_page_footer):
            foot = footer.paragraphs[0]
            foot.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
            _border(foot, "top", RULE, 4, 6)
            small = {"size": 7.5, "colour": LABEL}
            _run(foot, "Produced locally by 4CE", **small)
            _run(foot, f"   ·   {self.reference}", **small)
            _run(foot, "\tPage ", **small)
            _field(foot, "PAGE", **small)
            _run(foot, " of ", **small)
            _field(foot, "NUMPAGES", **small)

    def _masthead(self) -> None:
        from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Cm

        doc = self.doc
        classification = (self.valves.classification or "").strip()
        organisation = (self.valves.organisation or "").strip()

        # The rule under the masthead is the table's own bottom edge: a border on
        # an empty paragraph vanished in Quick Look, table borders do not.
        bar = doc.add_table(rows=1, cols=3)
        _frame(bar, colour=LINE, outer=("bottom",))
        _padding(bar, 0, 0)
        _columns(bar, [1.55, 8.55, 6.5])
        mark, name, right = bar.rows[0].cells
        for cell in (mark, name, right):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        if self.logo:
            mark.paragraphs[0].add_run().add_picture(io.BytesIO(self.logo), height=Cm(1.2))
        word = name.paragraphs[0]
        # The wordmark, set like the app's: heavy sans, closed up.
        _run(word, "4CE", font=HEAD, size=18, colour=INK, bold=True, track=-0.4)
        _pad(word, 0.1, 0, 0, 1.0)
        tagline = name.add_paragraph()
        _run(tagline, "Sovereign AI Workbench", size=8.5, colour=MUTED, track=0.3)
        _pad(tagline, 0.1, 1, 9, 1.0)
        for paragraph in (word, tagline):
            paragraph.paragraph_format.right_indent = Cm(0.8)

        top = right.paragraphs[0]
        top.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _spacing(top, 0, 0, 1.0)
        if classification:
            _run(top, classification, size=7.5, colour=INDIGO, bold=True, caps=True, track=1.4)
        if organisation:
            org = right.add_paragraph()
            org.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            _spacing(org, 2, 0, 1.0)
            _run(org, organisation, size=8.5, colour=MUTED)

        kicker = doc.add_paragraph()
        _spacing(kicker, 26, 5, 1.0)
        _run(kicker, self.kind, size=8, colour=INDIGO, bold=True, caps=True, track=1.6)

        heading = doc.add_paragraph()
        _spacing(heading, 0, 10, 1.05)
        heading.paragraph_format.keep_with_next = True
        _run(heading, self.title, font=HEAD, size=24, colour=INK, track=-0.4)

        accent = doc.add_paragraph()
        _spacing(accent, 0, 18, 1.0)
        accent.add_run().add_picture(io.BytesIO(_solid_png(ACCENT, 160, 10)), width=Cm(1.5), height=Cm(0.09))

        fields = [
            ("Reference", self.reference),
            ("Issued", f"{self.issued.day} {self.issued:%B %Y}, {self.issued:%H:%M} {self.issued.tzname() or ''}".strip()),
            # The answer's fingerprint in place of "Prepared by", which only
            # repeated the masthead. Grouped for reading aloud; the full hash
            # is in the verification record.
            (
                ("Fingerprint", " ".join(self.signoff["fingerprint"][i:i + 4] for i in range(0, 16, 4)))
                if self.signoff.get("fingerprint")
                else ("Prepared by", (self.valves.prepared_by or "").strip() or "4CE")
            ),
        ]
        if self.signoff.get("verification"):
            fields.append(("Verification", self.signoff["verification"]))
        if self.signoff.get("approved_by"):
            fields.append(("Approved by", self.signoff["approved_by"]))
        if self.signoff.get("models"):
            fields.append(("Models", self.signoff["models"]))

        rows = (len(fields) + 2) // 3
        panel = doc.add_table(rows=rows, cols=3)
        _frame(panel)
        _padding(panel, 0, 0)
        _columns(panel, [TEXT_W / 3] * 3)
        for index, cell in enumerate(c for row in panel.rows for c in row.cells):
            _shade_cell(cell, PAPER)
            if index >= len(fields):
                continue
            label, value = fields[index]
            first = cell.paragraphs[0]
            _pad(first, 0.3, 7, 1, 1.0)
            _run(first, label, size=7, colour=LABEL, bold=True, caps=True, track=1.0)
            second = cell.add_paragraph()
            _pad(second, 0.3, 0, 8, 1.15)
            _run(second, value, size=9.5, colour=INK)

        gap = doc.add_paragraph()
        _spacing(gap, 0, 6, 1.0)
        _run(gap, "", size=4)

    # -- body --------------------------------------------------------------

    def _markdown(self, text: str) -> None:
        lines = text.replace("\r\n", "\n").replace("\t", "    ").split("\n")
        prose: list[str] = []

        # The body's top headings sit at Heading 2, level with the report's own
        # Sources and Verification record, so the outline in Word reads as one
        # list of sections. An answer's sections are ### in the chat.
        levels, fenced = [], False
        for line in lines:
            if _FENCE.match(line):
                fenced = not fenced
            elif not fenced and _HEADING.match(line):
                levels.append(len(_HEADING.match(line).group(1)))
        # With no headings at all, a bold label line is a top section too.
        self._shift = 2 - min(levels) if levels else -1

        def flush() -> None:
            if prose:
                self._paragraph(" ".join(s.strip() for s in prose))
                prose.clear()

        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                flush()
                i += 1
            elif _FENCE.match(line):
                flush()
                block, i = [], i + 1
                while i < len(lines) and not _FENCE.match(lines[i]):
                    block.append(lines[i])
                    i += 1
                self._code(block)
                i += 1
            elif _IMAGE_LINE.match(line):
                flush()
                alt, file_id = _IMAGE_LINE.match(line).groups()
                self._image(file_id, alt)
                i += 1
            elif line.lstrip().startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
                flush()
                rows = []
                while i < len(lines) and lines[i].lstrip().startswith("|"):
                    rows.append(lines[i])
                    i += 1
                self._table(rows)
            elif _HEADING.match(line):
                flush()
                marks, words = _HEADING.match(line).groups()
                self._heading(words, max(2, min(len(marks) + self._shift, 4)))
                i += 1
            elif _RULE_LINE.match(line):
                flush()
                self._rule()
                i += 1
            elif _QUOTE.match(line):
                flush()
                quoted = []
                while i < len(lines) and _QUOTE.match(lines[i]):
                    quoted.append(_QUOTE.match(lines[i]).group(1))
                    i += 1
                self._quote(quoted)
            elif _ITEM.match(line):
                flush()
                items: list[list] = []
                while i < len(lines):
                    current = lines[i]
                    found = _ITEM.match(current)
                    if found:
                        indent, marker, words = found.groups()
                        items.append([len(indent), marker[0].isdigit(), words, marker])
                    elif current.strip() and items and (current.startswith("  ") or not _looks_structural(current)):
                        # A wrapped item continues on the next line.
                        items[-1][2] += " " + current.strip()
                    else:
                        break
                    i += 1
                self._list(items)
            else:
                prose.append(line)
                i += 1
        flush()

    def _paragraph(self, text: str) -> None:
        label = _LABEL_ONLY.match(text.strip())
        if label:
            # "**Working:**" alone on a line is a section label the model wrote
            # as bold text; it reads as the heading it is.
            self._heading(label.group(1).rstrip(" :"), max(2, min(3 + getattr(self, "_shift", 0), 4)))
            return
        paragraph = self.doc.add_paragraph()
        self._inline(paragraph, text)

    def _heading(self, text: str, level: int) -> None:
        paragraph = self.doc.add_paragraph(style=f"Heading {level}")
        self._inline(paragraph, _clean(text), heading=True)

    def _image(self, file_id: str, alt: str) -> None:
        """The picture itself, the width of the text, with its caption. A link
        would open nothing for someone reading the file away from 4CE."""
        from docx.shared import Cm

        data = self.images.get(file_id)
        if data:
            paragraph = self.doc.add_paragraph()
            _spacing(paragraph, 4, 2, 1.0)
            try:
                paragraph.add_run().add_picture(io.BytesIO(data), width=Cm(TEXT_W))
            except Exception:
                data = None
        caption = self.doc.add_paragraph()
        _spacing(caption, 0, 8, 1.15)
        _run(caption, (alt.strip() or "Image") + ("" if data else " - held in 4CE, not embedded"),
             size=9, colour=MUTED, italic=True)

    def _rule(self) -> None:
        paragraph = self.doc.add_paragraph()
        _spacing(paragraph, 4, 10, 1.0)
        _border(paragraph, "bottom", LINE, 6, 1)
        _run(paragraph, "", size=2)

    def _quote(self, lines: list[str]) -> None:
        chunks, chunk = [], []
        for line in lines + [""]:
            if line.strip():
                chunk.append(line.strip())
            elif chunk:
                chunks.append(" ".join(chunk))
                chunk = []
        cell = self._callout(INDIGO)
        for index, words in enumerate(chunks):
            paragraph = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
            paragraph.style = self.doc.styles["4CE Quote"]
            _pad(paragraph, 0.4, 7 if index == 0 else 0, 7 if index == len(chunks) - 1 else 4, 1.3)
            self._inline(paragraph, words)
        self._gap(8)

    def _code(self, lines: list[str]) -> None:
        lines = lines or [""]
        cell = self._callout(None)
        for index, line in enumerate(lines):
            paragraph = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
            paragraph.style = self.doc.styles["4CE Code"]
            _pad(paragraph, 0.35, 6 if index == 0 else 0, 6 if index == len(lines) - 1 else 0, 1.15)
            paragraph.add_run(line.rstrip() or " ")
        self._gap(8)

    def _callout(self, bar: str | None) -> Any:
        """A full-width shaded box - one cell, so every reader draws the fill."""
        table = self.doc.add_table(rows=1, cols=1)
        _frame(table)
        _padding(table, 0, 0)
        _columns(table, [TEXT_W])
        cell = table.rows[0].cells[0]
        _shade_cell(cell, PAPER)
        if bar:
            _put(cell._tc.get_or_add_tcPr(), _tc_borders(left=(bar, 18)))
        return cell

    def _gap(self, points: float) -> None:
        """Space after a table; also keeps two tables from fusing into one."""
        gap = self.doc.add_paragraph()
        _spacing(gap, 0, points, 1.0)
        _run(gap, "", size=4)

    def _list(self, items: list[list]) -> None:
        if not items:
            return
        self.lists += 1
        base = min(item[0] for item in items)
        numbers: dict[str, int] = {}
        for indent, ordered, words, marker in items:
            level = min(2, max(0, (indent - base) // 2))
            style = ("List Number" if ordered else "List Bullet") + ("" if level == 0 else f" {level + 1}")
            paragraph = self.doc.add_paragraph(style=style)
            if ordered:
                if style not in numbers:
                    start = int(re.match(r"\d+", marker).group()) if marker[0].isdigit() else 1
                    numbers[style] = self._restart(style, start)
                num_pr = paragraph._p.get_or_add_pPr().get_or_add_numPr()
                num_pr.get_or_add_ilvl().val = 0
                num_pr.get_or_add_numId().val = numbers[style]
            self._inline(paragraph, words)

    def _restart(self, style: str, start: int) -> int:
        """A fresh numbering instance, so each list counts from its own start.

        Every "List Number" paragraph otherwise shares one counter, and the
        second list in a document carries on from where the first stopped.
        """
        numbering = self.doc.part.numbering_part.numbering_definitions._numbering
        style_num = self.doc.styles[style].element.pPr.numPr.numId.val
        abstract = numbering.num_having_numId(style_num).abstractNumId.val
        num = numbering.add_num(abstract)
        num.add_lvlOverride(ilvl=0).add_startOverride(start)
        return num.numId

    def _table(self, lines: list[str]) -> None:
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        rows = [_cells(line) for index, line in enumerate(lines) if index != 1]
        align = [
            WD_ALIGN_PARAGRAPH.RIGHT if c.strip().endswith(":") and not c.strip().startswith(":")
            else WD_ALIGN_PARAGRAPH.CENTER if c.strip().startswith(":") and c.strip().endswith(":")
            else WD_ALIGN_PARAGRAPH.LEFT
            for c in _cells(lines[1])
        ]
        count = max(len(r) for r in rows)
        rows = [r + [""] * (count - len(r)) for r in rows]
        align += [WD_ALIGN_PARAGRAPH.LEFT] * (count - len(align))

        # Share the width by how much each column says, within limits, so a
        # column of short codes does not get the same room as the prose - but
        # never less than its longest word. Shared by length alone, an
        # eight-column table of readings broke "P-101B" as "P-/101B" and
        # "02:10" as "02:1/0".
        per_char, pad = 0.19, 0.4  # cm: 9.5 pt Arial, and the cell's own padding
        texts = [[_clean(r[c]) for r in rows] for c in range(count)]
        least = [pad + per_char * max([len(word) for text in col for word in text.split()] or [1]) for col in texts]
        want = [max(low, pad + per_char * min(40, max(len(text) for text in col))) for low, col in zip(least, texts)]
        if sum(want) <= TEXT_W:
            widths = [TEXT_W * w / sum(want) for w in want]
        elif sum(least) >= TEXT_W:
            widths = [TEXT_W * w / sum(least) for w in least]
        else:
            spare = TEXT_W - sum(least)
            extra = [w - low for w, low in zip(want, least)]
            widths = [low + spare * e / sum(extra) for low, e in zip(least, extra)]

        table = self.doc.add_table(rows=len(rows), cols=count)
        _frame(table, outer=("top", "bottom"), inside_h=True)
        _padding(table, 0, 0)
        _columns(table, widths)
        _put(table.rows[0]._tr.get_or_add_trPr(), _el("w:tblHeader"))  # repeat on each page
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                cell = table.rows[r].cells[c]
                paragraph = cell.paragraphs[0]
                paragraph.alignment = align[c]
                _pad(paragraph, 0.15, 3.5, 3.5, 1.15)
                if r == 0:
                    _shade_cell(cell, FILL)
                    self._inline(paragraph, value, size=8.5, colour=INK, bold=True)
                else:
                    self._inline(paragraph, value, size=9.5)
        self._gap(6)

    def _inline(self, paragraph: Any, text: str, heading: bool = False, **base: Any) -> None:
        text = _clean(text)
        position = 0
        for match in _INLINE.finditer(text):
            if match.start() > position:
                _run(paragraph, _unescape(text[position:match.start()]), **base)
            group = match.lastgroup
            value = match.group(group)
            if group == "bi":
                self._inline(paragraph, value, **{**base, "bold": True, "italic": True})
            elif group in ("b", "b2"):
                self._inline(paragraph, value, **{**base, "bold": True})
            elif group in ("i", "i2"):
                self._inline(paragraph, value, **{**base, "italic": True})
            elif group == "code":
                size = base.get("size") or (None if heading else 9.5)
                _run(paragraph, value, **{**base, "font": MONO, "size": size, "fill": None if heading else PAPER})
            elif group == "cite":
                # A source number from the chat's [n]: a superscript that points
                # at the Sources list at the end of the document.
                numbers = ",".join(n.strip() for n in value.split(","))
                _run(paragraph, numbers, **{**base, "colour": INDIGO, "bold": True, "sup": True})
            elif group == "link":
                _run(paragraph, _unescape(value), **{**base, "colour": INDIGO, "underline": True})
                url = match.group("url")
                if url.strip() != value.strip():
                    _run(paragraph, f" ({url})", **{**base, "colour": MUTED})
            position = match.end()
        if position < len(text):
            _run(paragraph, _unescape(text[position:]), **base)

    # -- end matter --------------------------------------------------------

    def _sources(self) -> None:
        self._heading("Sources", 2)
        note = self.doc.add_paragraph()
        _spacing(note, 0, 8, 1.2)
        _run(
            note,
            "The documents 4CE retrieved from the local knowledge base. Each raised "
            "number in the text refers to one of them.",
            size=9,
            colour=MUTED,
        )
        for n, name in enumerate(self.sources, 1):
            line = self.doc.add_paragraph()
            _spacing(line, 0, 3, 1.2)
            line.paragraph_format.keep_with_next = True
            _run(line, f"{n}", size=9.5, colour=INDIGO, bold=True)
            _run(line, f"\u2003{name}", size=10, colour=INK)
            cited = self.cited is None or n in self.cited
            if self.cited is not None:
                _run(line, "\u2003cited" if cited else "\u2003retrieved, not cited", size=8.5, colour=LABEL)
            # What the answer's [n] rests on: the passage 4CE retrieved.
            if cited and n - 1 < len(self.passages) and self.passages[n - 1].strip():
                self._excerpt(self.passages[n - 1])
        self._gap(6)

    def _excerpt(self, text: str, limit: int = 900) -> None:
        from docx.shared import Pt

        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines, used = [line for line in lines if line], 0
        kept = []
        for line in lines:
            if used + len(line) > limit:
                kept.append("…")
                break
            kept.append(line)
            used += len(line)
        for index, line in enumerate(kept):
            paragraph = self.doc.add_paragraph()
            _spacing(paragraph, 0, 6 if index == len(kept) - 1 else 0, 1.2)
            paragraph.paragraph_format.left_indent = Pt(17)
            _run(paragraph, line, size=8.5, colour=MUTED)

    def _checks(self) -> None:
        """The checks made on the answer before it was released, as in the
        chat's "What was checked" card: 4CE's own figure check first, made
        without a model, then ULTRON's."""
        from docx.shared import Pt

        self._heading("What was checked", 2)
        note = self.doc.add_paragraph()
        _spacing(note, 0, 8, 1.2)
        _run(
            note,
            "The checks made on this answer before release. 4CE's figure check is made "
            "without a model; ULTRON's are its own reading.",
            size=9,
            colour=MUTED,
        )
        marks = {"ok": ("\u2713", GOOD), "problem": ("\u2715", ACCENT)}
        for check in self.checks:
            mark, colour = marks.get(check.get("kind"), ("\u2013", LABEL))
            paragraph = self.doc.add_paragraph()
            _spacing(paragraph, 0, 3, 1.2)
            paragraph.paragraph_format.left_indent = Pt(14)
            paragraph.paragraph_format.first_line_indent = Pt(-14)
            _run(paragraph, f"{mark}\u2002", size=10, colour=colour, bold=True)
            _run(paragraph, str(check["text"]), size=10, colour=BODY)
            if check.get("by"):
                _run(paragraph, f"\u2003{check['by']}", size=7, colour=LABEL, bold=True, caps=True, track=1.0)
        self._gap(6)

    def _revisions(self) -> None:
        """What the verifier objected to in the first draft, the lines changed
        for it, and the verdict on the revised draft - as in the chat's
        "What changed on try 2" card."""
        from docx.shared import Pt

        rev = self.revision
        changes = rev.get("changes") or []
        self._heading("Revisions", 2)
        note = self.doc.add_paragraph()
        _spacing(note, 0, 8, 1.2)
        _run(
            note,
            f"{rev.get('by') or 'ULTRON'} sent the first draft back. What it objected to, what "
            "JARVIS changed for it, and the verdict on the revised draft.",
            size=9,
            colour=MUTED,
        )

        def line(label: str, text: str, colour: str, after: float = 2) -> None:
            paragraph = self.doc.add_paragraph()
            _spacing(paragraph, 0, after, 1.2)
            paragraph.paragraph_format.left_indent = Pt(12)
            _run(paragraph, f"{label}\u2003", size=7, colour=LABEL, bold=True, caps=True, track=1.0)
            _run(paragraph, text, size=10, colour=colour)

        fixed = set()
        for objection in rev["objections"]:
            line("Objection", objection.get("text", ""), INK, 2)
            for i in objection.get("fixes") or []:
                if i < len(changes):
                    fixed.add(i)
                    if changes[i].get("removed"):
                        line("Was", changes[i]["removed"], MUTED)
                    if changes[i].get("added"):
                        line("Now", changes[i]["added"], INK)
            self._gap(4)
        passed = str(rev.get("verdict", "")).upper() == "PASS"
        others = len(changes) - len(fixed) + int(rev.get("more") or 0)
        line(
            "Verdict",
            ("ULTRON passed the revised draft." if passed else "ULTRON failed the revised draft as well.")
            + (f" {others} other {'edit' if others == 1 else 'edits'} were made along the way." if others else ""),
            INK,
            6,
        )

    def _record(self) -> None:
        self._heading("Verification record", 2)
        note = self.doc.add_paragraph()
        _spacing(note, 0, 8, 1.2)
        _run(note, "How this document was produced, as recorded by the 4CE agent chain.", size=9, colour=MUTED)

        table = self.doc.add_table(rows=len(self.record), cols=2)
        _frame(table, outer=("top", "bottom"), inside_h=True)
        _padding(table, 0, 0)
        _columns(table, [4.1, TEXT_W - 4.1])
        for r, (label, value) in enumerate(self.record):
            left, right = table.rows[r].cells
            first = left.paragraphs[0]
            _pad(first, 0.15, 5, 3.5, 1.15)
            _run(first, label, size=7.5, colour=LABEL, bold=True, caps=True, track=0.8)
            second = right.paragraphs[0]
            _pad(second, 0.15, 3.5, 3.5, 1.2)
            self._inline(second, value, size=9.5)
        self._gap(12)

    def _signoff(self) -> None:
        """The release statement: who approved it, when, and on what check."""
        cell = self._callout(ACCENT)
        head = cell.paragraphs[0]
        _pad(head, 0.45, 10, 4, 1.0)
        _run(head, "Released after human approval", size=7.5, colour=INDIGO, bold=True, caps=True, track=1.4)
        statement = cell.add_paragraph()
        _pad(statement, 0.45, 0, 0, 1.3)
        _run(statement, f"Approved by {self.signoff['approved_by']}", size=10, colour=INK, bold=True)
        when = self.signoff.get("approved_at")
        _run(statement, f" in 4CE{f' on {when}' if when else ''}.", size=10, colour=INK)
        detail = [
            "This document was produced only after that approval",
        ]
        if self.signoff.get("verification"):
            detail.append(f"ULTRON's independent check returned {self.signoff['verification']}")
        tail = cell.add_paragraph()
        _pad(tail, 0.45, 3, 11, 1.3)
        _run(tail, "; ".join(detail) + ".", size=9, colour=MUTED)

    def _properties(self) -> None:
        props = self.doc.core_properties
        props.title = self.title
        props.subject = self.kind
        props.author = (self.valves.prepared_by or "").strip() or "4CE"
        props.keywords = "4CE"
        props.category = (self.valves.classification or "").strip()
        props.comments = f"Reference {self.reference}"


def _spacing_style(style: Any, before: float, after: float, line: float) -> None:
    from docx.shared import Pt

    fmt = style.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def _tc_borders(**sides: tuple) -> Any:
    borders = _el("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        if edge in sides:
            colour, eighths = sides[edge]
            borders.append(_el(f"w:{edge}", val="single", sz=eighths, space=0, color=colour))
    return borders


def _pt(points: float) -> Any:
    from docx.shared import Pt

    return Pt(points)


def _looks_structural(line: str) -> bool:
    return bool(_HEADING.match(line) or _QUOTE.match(line) or _FENCE.match(line) or line.lstrip().startswith("|"))


def _cells(line: str) -> list[str]:
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", row)]


def _clean(text: str) -> str:
    """Drop the HTML a model sometimes mixes into markdown; keep the words."""
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    return re.sub(r"</?[a-zA-Z][^>]*>", "", text)


def _unescape(text: str) -> str:
    return re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>])", r"\1", text)


# ---------------------------------------------------------------------------
# Workbooks and decks
#
# Both are built from the released answer itself, parsed once into neutral
# blocks, so a workbook's figures and a deck's bullets are the approved text -
# nothing is re-asked of a model. Same house style as the report: ink, warm
# paper, one deep-orange accent, Arial.
# ---------------------------------------------------------------------------


def _refusal(title: str, body: str, user: dict | None) -> str:
    if not (title or "").strip():
        return "A title is required."
    if not (body or "").strip():
        return "The content is empty; nothing was generated."
    if not user or not user.get("id"):
        return "The file could not be attributed to a user, so it was not generated."
    return ""


def _blocks(text: str) -> list[tuple]:
    """An answer as ("heading", level, text), ("para", text), ("list", [items]),
    ("table", header, rows), ("code", text) and ("image", alt, file_id)
    blocks, in order."""
    lines = (text or "").replace("\r\n", "\n").replace("\t", "    ").split("\n")
    out: list[tuple] = []
    prose: list[str] = []

    def flush() -> None:
        if prose:
            out.append(("para", " ".join(s.strip() for s in prose)))
            prose.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush()
            i += 1
        elif _FENCE.match(line):
            flush()
            block, i = [], i + 1
            while i < len(lines) and not _FENCE.match(lines[i]):
                block.append(lines[i])
                i += 1
            out.append(("code", "\n".join(block)))
            i += 1
        elif _IMAGE_LINE.match(line):
            flush()
            alt, file_id = _IMAGE_LINE.match(line).groups()
            out.append(("image", alt, file_id))
            i += 1
        elif line.lstrip().startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            flush()
            header, i = _cells(line), i + 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            out.append(("table", header, rows))
        elif _HEADING.match(line):
            flush()
            marks, words = _HEADING.match(line).groups()
            out.append(("heading", len(marks), words))
            i += 1
        elif _RULE_LINE.match(line):
            flush()
            i += 1
        elif _QUOTE.match(line):
            flush()
            quoted = []
            while i < len(lines) and _QUOTE.match(lines[i]):
                quoted.append(_QUOTE.match(lines[i]).group(1))
                i += 1
            out.append(("para", " ".join(q.strip() for q in quoted if q.strip())))
        elif _ITEM.match(line):
            flush()
            items: list[str] = []
            while i < len(lines):
                found = _ITEM.match(lines[i])
                if found:
                    items.append(found.group(3))
                elif lines[i].strip() and items and (lines[i].startswith("  ") or not _looks_structural(lines[i])):
                    items[-1] += " " + lines[i].strip()
                else:
                    break
                i += 1
            out.append(("list", items))
        else:
            prose.append(line)
            i += 1
    flush()
    return out


def _plain(text: str) -> str:
    """Inline markdown as the words a cell or a slide shows. Citation numbers stay."""
    text = _clean(text or "")
    text = re.sub(r"!?\[([^\]]+)\]\([^)\s]+\)", r"\1", text)
    text = re.sub(r"\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|__(.+?)__", lambda m: next(g for g in m.groups() if g), text)
    text = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return _unescape(text).strip()


_NUMBER = re.compile(r"^([-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(%|[^\d\s].{0,15}?)?$")


def _numeric(cell: str) -> tuple[float, str] | None:
    """A cell that is one number and, optionally, its unit: (value, unit).
    Anything else - a range, a comparison, a citation, words - is not."""
    text = _plain(cell)
    found = _NUMBER.match(text)
    if not found:
        return None
    value = float(found.group(1).replace(",", "").replace("−", "-"))
    return value, (found.group(2) or "").strip()


def _sheet_name(name: str, used: set[str]) -> str:
    base = re.sub(r"[\[\]:*?/\\]", " ", _plain(name)).strip()[:28] or "Sheet"
    candidate, n = base, 2
    while candidate.lower() in used:
        candidate, n = f"{base[:25]} {n}", n + 1
    used.add(candidate.lower())
    return candidate


def _build_xlsx(title: str, body: str, record: list, sources: list, calculations: list | None = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    ink, muted = Font(name=SANS, color=INK), Font(name=SANS, color=MUTED, size=9)
    bold = Font(name=SANS, color=INK, bold=True)
    fill = PatternFill("solid", fgColor=FILL)
    rule = Border(bottom=Side(style="thin", color=LINE))
    wrap = Alignment(wrap_text=True, vertical="top")

    book = Workbook()
    book.remove(book.active)
    used: set[str] = set()
    heading, tables, prose = "", 0, []

    for block in _blocks(body):
        if block[0] == "heading":
            heading = block[2]
            prose.append((True, _plain(block[2])))
        elif block[0] == "para":
            prose.append((False, _plain(block[1])))
        elif block[0] == "list":
            prose += [(False, "• " + _plain(item)) for item in block[1]]
        elif block[0] == "table":
            tables += 1
            sheet = book.create_sheet(_sheet_name(heading or f"Table {tables}", used))
            _write_table(sheet, block[1], block[2], bold, ink, fill, rule, get_column_letter)

    # A calculation 4CE ran is rebuilt as live formulas over its inputs, first
    # in the workbook: change an input and the rest recalculates.
    for calculation in calculations or []:
        if calculation.get("kind") == "remaining_life" and calculation.get("rows"):
            _remaining_life_sheet(book, calculation, used, bold, fill, rule, get_column_letter)

    # The answer's words, for a request that asked for a workbook of
    # something that is not a table.
    if prose:
        notes = book.create_sheet(_sheet_name("Notes", used))
        notes.column_dimensions["A"].width = 110
        for row, (is_heading, line) in enumerate(prose, 1):
            cell = notes.cell(row=row, column=1, value=line)
            cell.font, cell.alignment = (bold if is_heading else ink), wrap

    about = book.create_sheet(_sheet_name("About this workbook", used))
    about.column_dimensions["A"].width, about.column_dimensions["B"].width = 24, 90
    about.cell(row=1, column=1, value=_plain(title)).font = Font(name=SANS, color=INK, bold=True, size=14)
    about.cell(row=2, column=1, value=(
        "Produced by 4CE on this machine with local open-weight models. The figures are the "
        "released answer's own; the only formulas are totals that were checked to add up."
    )).font = muted
    row = 4
    for label, value in record:
        about.cell(row=row, column=1, value=str(label)).font = bold
        cell = about.cell(row=row, column=2, value=_plain(str(value)))
        cell.font, cell.alignment = ink, wrap
        row += 1
    if sources:
        row += 1
        about.cell(row=row, column=1, value="Sources").font = bold
        for n, name in enumerate(sources, 1):
            about.cell(row=row, column=2, value=f"[{n}] {name}").font = ink
            row += 1

    book.properties.title = _plain(title)
    book.properties.creator = "4CE"
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def _write_table(sheet, header, rows, bold, ink, fill, rule, letter) -> None:
    width = max([len(header)] + [len(r) for r in rows])
    header = list(header) + [""] * (width - len(header))
    rows = [list(r) + [""] * (width - len(r)) for r in rows]

    # A last row that says it is a total, checked below before it becomes one.
    total = bool(rows) and re.match(r"^\s*total\b", _plain(rows[-1][0]), re.I) is not None
    data = rows[:-1] if total else rows

    columns = []
    for c in range(width):
        parsed = [_numeric(r[c]) for r in data if _plain(r[c])]
        units = {p[1] for p in parsed if p}
        numeric = bool(parsed) and all(parsed) and len(units) == 1
        columns.append((numeric, units.pop() if numeric else ""))

    for c, name in enumerate(header):
        label = _plain(name)
        numeric, unit = columns[c]
        # "Reading" over "18 drops/min, 7.1 drops/min" becomes "Reading (drops/min)"
        # over numbers a formula can use.
        if numeric and unit and unit != "%" and unit.lower() not in label.lower():
            label = f"{label} ({unit})"
        cell = sheet.cell(row=1, column=c + 1, value=label)
        cell.font, cell.fill, cell.border = bold, fill, rule

    for r, row in enumerate(data, 2):
        for c, raw in enumerate(row):
            numeric, unit = columns[c]
            cell = sheet.cell(row=r, column=c + 1)
            parsed = _numeric(raw) if numeric else None
            if parsed:
                value = parsed[0] / 100 if unit == "%" else parsed[0]
                cell.value = int(value) if float(value).is_integer() and unit != "%" else value
                cell.number_format = "0%" if unit == "%" else ("0" if isinstance(cell.value, int) else "0.0##")
            else:
                cell.value = _plain(raw)
            cell.font = ink

    if total:
        r = len(data) + 2
        sheet.cell(row=r, column=1, value=_plain(rows[-1][0])).font = bold
        for c in range(1, width):
            numeric, unit = columns[c]
            stated = _numeric(rows[-1][c])
            cell = sheet.cell(row=r, column=c + 1)
            if numeric and stated and data:
                values = [p[0] for row in data if (p := _numeric(row[c]))]
                if abs(sum(values) - stated[0]) <= 1e-6 * max(1.0, abs(stated[0])):
                    col = letter(c + 1)
                    cell.value = f"=SUM({col}2:{col}{r - 1})"
                    cell.number_format = "0%" if unit == "%" else "0.0##"
                else:
                    cell.value = _plain(rows[-1][c])
            else:
                cell.value = _plain(rows[-1][c])
            cell.font = bold

    for c in range(width):
        cells = [_plain(header[c])] + [_plain(r[c]) for r in rows]
        sheet.column_dimensions[letter(c + 1)].width = min(60, max(10, max(len(v) for v in cells) + 2))
    sheet.freeze_panes = "A2"
    if data:
        sheet.auto_filter.ref = f"A1:{letter(width)}{len(data) + 1}"


def _remaining_life_sheet(book, calculation: dict, used: set, bold, fill, rule, letter) -> None:
    """Corrosion rate, remaining life and the next measurement as formulas, not values.

    The same thickness method as the calculation tool (4ce/tools/calculations.py):
    CR = (previous - current) / interval, RL = (current - required) / CR, and
    the next measurement at the lesser of RL / 2 and the code maximum.
    """
    from openpyxl.styles import Alignment, Font

    sheet = book.create_sheet(_sheet_name("Remaining life", used), 0)
    blue = Font(name=SANS, color="1F4E9E")  # an input: change it and the rest recalculates
    ink = Font(name=SANS, color=INK)
    header = [
        "Location", "Previous thickness (mm)", "Current thickness (mm)", "Required thickness (mm)",
        "Interval (years)", "Maximum interval (years)", "Corrosion rate (mm/year)",
        "Remaining life (years)", "Next measurement within (years)",
    ]
    for c, name in enumerate(header, 1):
        cell = sheet.cell(row=1, column=c, value=name)
        cell.font, cell.fill, cell.border = bold, fill, rule
        cell.alignment = Alignment(wrap_text=True, vertical="bottom")

    maximum = calculation.get("max_interval")
    rows = calculation["rows"]
    for r, row in enumerate(rows, 2):
        values = [row.get("location") or f"Location {r - 1}", row["previous"], row["current"],
                  row["required"], row["years"], row.get("max_interval", maximum)]
        for c, value in enumerate(values, 1):
            cell = sheet.cell(row=r, column=c, value=value)
            cell.font = blue if c > 1 else ink
            if c > 1:
                cell.number_format = "0.0##"
        formulas = [
            (f"=IF(E{r}>0,(B{r}-C{r})/E{r},\"\")", "0.000"),
            (f"=IF(C{r}<=D{r},0,IF(N(G{r})<=0,\"not corrosion-limited\",(C{r}-D{r})/G{r}))", "0.0"),
            # With no wall loss, an empty code maximum must not read as "within 0 years".
            (f"=IF(ISNUMBER(H{r}),IF(ISNUMBER(F{r}),MIN(H{r}/2,F{r}),H{r}/2),"
             f"IF(ISNUMBER(F{r}),F{r},\"the code's normal interval\"))", "0.0"),
        ]
        for c, (formula, number_format) in enumerate(formulas, 7):
            cell = sheet.cell(row=r, column=c, value=formula)
            cell.font, cell.number_format = ink, number_format

    note = len(rows) + 3
    sheet.cell(row=note, column=1, value=(
        "Blue cells are inputs; change one and the rest recalculate. Corrosion rate = (previous - "
        "current) / interval. Remaining life = (current - required) / corrosion rate, and 0 at or "
        "below the required thickness. Next measurement = the lesser of remaining life / 2 and the "
        "maximum interval, when one is given"
        + (f" - here {calculation['basis']}." if calculation.get("basis") else ".")
    )).font = Font(name=SANS, color=MUTED, size=9)
    widths = [14, 14, 14, 14, 11, 14, 14, 14, 16]
    for c, width in enumerate(widths, 1):
        sheet.column_dimensions[letter(c)].width = width
    sheet.row_dimensions[1].height = 32
    sheet.freeze_panes = "B2"


def _build_pptx(title: str, body: str, document_type: str, record: list, sources: list,
                images: dict | None = None) -> bytes:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import MSO_ANCHOR
    from pptx.util import Inches, Pt

    colour = {name: RGBColor.from_string(value) for name, value in
              (("ink", INK), ("body", BODY), ("muted", MUTED), ("accent", ACCENT), ("fill", FILL), ("rule", RULE))}
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    blank = deck.slide_layouts[6]
    heading_text = _plain(title)

    def text(slide, left, top, width, height, lines, size, colour_name="body", bold=False, font=SANS):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        frame = box.text_frame
        frame.word_wrap = True
        frame.vertical_anchor = MSO_ANCHOR.TOP
        for n, line in enumerate(lines if isinstance(lines, list) else [lines]):
            paragraph = frame.paragraphs[0] if n == 0 else frame.add_paragraph()
            paragraph.space_after = Pt(size * 0.5)
            # A (label, value) pair sets its label in bold, as the report's record does.
            for part, strong in ((line[0] + "  ", True), (line[1], bold)) if isinstance(line, tuple) else ((line, bold),):
                run = paragraph.add_run()
                run.text = part
                run.font.size, run.font.bold, run.font.name = Pt(size), strong, font
                run.font.color.rgb = colour["ink" if strong and isinstance(line, tuple) else colour_name]
        return box

    def slide(heading: str, notes: str = ""):
        page = deck.slides.add_slide(blank)
        bar = page.shapes.add_shape(1, Inches(0.6), Inches(0.55), Inches(0.08), Inches(0.55))
        bar.fill.solid()
        bar.fill.fore_color.rgb = colour["accent"]
        bar.line.fill.background()
        bar.shadow.inherit = False
        text(page, 0.85, 0.45, 11.8, 0.9, _plain(heading), 28, "ink", bold=True)
        text(page, 0.6, 6.95, 9.0, 0.35, f"4CE · {heading_text}", 10, "muted")
        text(page, 12.0, 6.95, 0.8, 0.35, str(len(deck.slides)), 10, "muted")
        if notes:
            page.notes_slide.notes_text_frame.text = notes
        return page

    def bullets(heading: str, items: list[str], notes: str) -> None:
        items = [_plain(i) for i in items if _plain(i)]
        for start in range(0, len(items), 6):
            chunk = items[start:start + 6]
            size = 20 if all(len(i) <= 140 for i in chunk) else 16
            page = slide(heading if start == 0 else f"{heading} (continued)", notes)
            text(page, 0.85, 1.6, 11.8, 5.2, ["• " + i for i in chunk], size)

    def table(heading: str, header: list[str], rows: list[list[str]], notes: str) -> None:
        width = max([len(header)] + [len(r) for r in rows])
        for start in range(0, max(1, len(rows)), 9):
            chunk = rows[start:start + 9]
            page = slide(heading if start == 0 else f"{heading} (continued)", notes)
            shape = page.shapes.add_table(len(chunk) + 1, width, Inches(0.85), Inches(1.6),
                                          Inches(11.8), Inches(0.45 * (len(chunk) + 1)))
            grid = shape.table
            for r, values in enumerate([header] + chunk):
                for c in range(width):
                    cell = grid.cell(r, c)
                    cell.text = _plain(values[c]) if c < len(values) else ""
                    for paragraph in cell.text_frame.paragraphs:
                        for run in paragraph.runs:
                            run.font.size, run.font.name = Pt(14 if r == 0 else 13), SANS
                            run.font.bold = r == 0
                            run.font.color.rgb = colour["ink"]
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = colour["fill"] if r == 0 else RGBColor(0xFF, 0xFF, 0xFF)

    # Title.
    first = deck.slides.add_slide(blank)
    text(first, 0.9, 2.1, 11.5, 0.5, (document_type or "Deliverable").upper(), 14, "accent", bold=True)
    text(first, 0.9, 2.6, 11.5, 2.2, heading_text, 40, "ink", bold=True)
    text(first, 0.9, 5.2, 11.5, 0.5, f"4CE · {datetime.now():%d %B %Y} · produced on this machine", 14, "muted")

    # Sections: the opening answer first, then each heading's content.
    sections: list[tuple[str, list[tuple]]] = [("In short", [])]
    for block in _blocks(body):
        if block[0] == "heading":
            sections.append((block[2], []))
        else:
            sections[-1][1].append(block)
    for heading, blocks in sections:
        if not blocks:
            continue
        notes = "\n".join(
            _plain(b[1]) if b[0] in ("para", "code", "image") else
            "\n".join("- " + _plain(i) for i in b[1]) if b[0] == "list" else
            " | ".join(_plain(c) for c in b[1]) for b in blocks
        )
        if sources:
            notes += "\n\nSources: " + "; ".join(f"[{n}] {s}" for n, s in enumerate(sources, 1))
        items: list[str] = []
        for block in blocks:
            if block[0] == "para":
                items.append(block[1])
            elif block[0] == "list":
                items += block[1]
            elif block[0] == "table":
                if items:
                    bullets(heading, items, notes)
                    items = []
                table(heading, block[1], block[2], notes)
            elif block[0] == "image" and (images or {}).get(block[2]):
                if items:
                    bullets(heading, items, notes)
                    items = []
                page = slide(heading, notes)
                picture = page.shapes.add_picture(io.BytesIO(images[block[2]]), Inches(0.85), Inches(1.5))
                # Fitted inside the slide below the heading, keeping its shape.
                scale = min(Inches(11.8) / picture.width, Inches(5.0) / picture.height)
                picture.width, picture.height = int(picture.width * scale), int(picture.height * scale)
                picture.left = int((deck.slide_width - picture.width) / 2)
                if block[1].strip():
                    text(page, 0.85, 6.55, 11.8, 0.35, _plain(block[1]), 11, "muted")
            elif block[0] == "code":
                if items:
                    bullets(heading, items, notes)
                    items = []
                page = slide(heading, notes)
                lines = block[1].splitlines()
                shown = lines[:18] + (["…"] if len(lines) > 18 else [])
                text(page, 0.85, 1.6, 11.8, 5.2, "\n".join(shown), 12, "ink", font=MONO)
        if items:
            if heading == "In short":
                page = slide(heading, notes)
                text(page, 0.85, 1.7, 11.8, 5.0, [_plain(i) for i in items], 24, "ink")
            else:
                bullets(heading, items, notes)

    # How it was produced: the record, as the report and the chat carry it.
    if record or sources:
        page = slide("How this was produced")
        keep = [(str(l), _plain(str(v))) for l, v in record
                if str(l) in ("Model routed", "Verification", "Human approval", "Egress", "Fingerprint", "Grounding")]
        lines = list(keep)
        if sources:
            lines.append(("Sources", "; ".join(f"[{n}] {s}" for n, s in enumerate(sources, 1))))
        text(page, 0.85, 1.6, 11.8, 5.2, lines, 16)

    deck.core_properties.title = heading_text
    deck.core_properties.author = "4CE"
    buffer = io.BytesIO()
    deck.save(buffer)
    return buffer.getvalue()


async def _load_images(body: str) -> dict[str, bytes]:
    """The images an answer shows, read from this machine's file store by id.
    Only images: a link to anything else stays a link."""
    images: dict[str, bytes] = {}
    for file_id in dict.fromkeys(m.group(2) for m in _IMAGE_LINE.finditer(body or "")):
        try:
            record = await Files.get_file_by_id(file_id)
            if not record or not str((record.meta or {}).get("content_type", "")).startswith("image/"):
                continue
            local = await asyncio.to_thread(Storage.get_file, record.path)
            images[file_id] = await asyncio.to_thread(Path(local).read_bytes)
        except Exception:
            continue
    return images


async def _emit(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})
