"""
title: 4CE Spreadsheets
author: 4CE
version: 0.1.0
description: Reads an Excel workbook or a CSV - attached to the chat or in 4CE's workspace - as tables with their cell references and formulas, and writes changes to a copy, never the source, as live formulas. Every read and write is recorded in 4CE's audit trail.
"""

import ast
import asyncio
import csv
import hashlib
import io
import json
import math
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

SHEET_TYPES = (".xlsx", ".xlsm", ".csv", ".tsv")
VERSIONS = ".versions"

# A formula that could reach outside the workbook - a web service, another
# file, a DDE link to a program, a hyperlink out - is refused. The copy opens
# in Excel on a plant PC, and a formula is code there.
_UNSAFE = re.compile(
    r"\[|\||://|\\\\|\b(?:WEBSERVICE|FILTERXML|CALL|REGISTER(?:\.ID)?|EXEC|RTD|DDE|IMPORT[A-Z]*|"
    r"HYPERLINK|INDIRECT|OFFSET|INFO|CELL)\s*\(",
    re.I,
)
_REF = re.compile(r"(?<![A-Za-z_\"])\$?([A-Z]{1,3})\$?([1-9][0-9]{0,6})(?![0-9A-Za-z_(])")
_RANGE = re.compile(r"\$?([A-Z]{1,3})\$?([1-9][0-9]{0,6}):\$?([A-Z]{1,3})\$?([1-9][0-9]{0,6})")


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
    raw = str(requested or "").strip().replace("\\", "/")
    if not raw or "\x00" in raw or raw.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", raw):
        return None
    base = root.resolve()
    target = (base / raw).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None
    return target if target != base else None


# ---------------------------------------------------------------------------
# Cells
# ---------------------------------------------------------------------------


def _column_number(letters: str) -> int:
    n = 0
    for ch in letters.upper():
        n = n * 26 + ord(ch) - 64
    return n


def _column_letters(n: int) -> str:
    letters = ""
    while n:
        n, rest = divmod(n - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def _shown(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "#NUM!"
        return f"{value:.6g}"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value).replace("|", "/").replace("\n", " ").strip()


class _Grid:
    """A sheet's cells, with formulas evaluated on demand - the values a copy
    will show when Excel opens it."""

    def __init__(self, cells: dict[str, Any], cached: dict[str, Any] | None = None):
        self.cells = cells
        self.cached = cached or {}
        self._busy: set[str] = set()
        self._done: dict[str, Any] = {}

    def value(self, ref: str) -> Any:
        ref = ref.replace("$", "").upper()
        if ref in self._done:
            return self._done[ref]
        raw = self.cells.get(ref)
        if isinstance(raw, str) and raw.startswith("="):
            if ref in self._busy:
                return "#REF!"
            self._busy.add(ref)
            try:
                result = _evaluate(raw, self)
            finally:
                self._busy.discard(ref)
            if isinstance(result, str) and result.startswith("#") and self.cached.get(ref) is not None:
                result = self.cached[ref]
        else:
            result = raw
        self._done[ref] = result
        return result

    def span(self, start: str, end: str) -> list[Any]:
        a, b = _REF.fullmatch(start), _REF.fullmatch(end)
        c1, c2 = sorted((_column_number(a.group(1)), _column_number(b.group(1))))
        r1, r2 = sorted((int(a.group(2)), int(b.group(2))))
        return [self.value(f"{_column_letters(c)}{r}") for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


# ---------------------------------------------------------------------------
# A formula evaluator: arithmetic, comparisons and a handful of functions,
# walked node by node - nothing is handed to eval().
# ---------------------------------------------------------------------------

_ALLOWED = {"MIN", "MAX", "ABS", "ROUND", "IF", "N", "ISNUMBER", "SUM", "AVERAGE", "AND", "OR", "NOT", "SQRT"}


class _FormulaError(Exception):
    pass


def _number(v: Any) -> float:
    if v is None or v == "":
        return 0.0
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str) and v.startswith("#"):
        raise _FormulaError(v)
    try:
        return float(str(v))
    except ValueError:
        raise _FormulaError("#VALUE!")


def _flat(values: list) -> list:
    out: list = []
    for v in values:
        out.extend(_flat(v) if isinstance(v, list) else [v])
    return out


def _evaluate(formula: str, grid: _Grid) -> Any:
    expr = formula.strip()[1:] if formula.strip().startswith("=") else formula.strip()
    if _UNSAFE.search(expr):
        return "#BLOCKED!"
    # Excel's operators, as Python writes them; strings kept as they are.
    parts = re.split(r'("(?:[^"]|"")*")', expr)
    for i in range(0, len(parts), 2):
        piece = parts[i].replace("<>", "!=").replace("^", "**")
        piece = re.sub(r"(?<![<>!=])=(?!=)", "==", piece)
        piece = _RANGE.sub(lambda m: f'__span("{m.group(1)}{m.group(2)}","{m.group(3)}{m.group(4)}")', piece)
        piece = _REF.sub(lambda m: f'__ref("{m.group(1)}{m.group(2)}")', piece)
        piece = re.sub(r"\bTRUE\b", "True", piece, flags=re.I)
        piece = re.sub(r"\bFALSE\b", "False", piece, flags=re.I)
        parts[i] = piece
    try:
        tree = ast.parse("".join(parts), mode="eval")
        return _walk(tree.body, grid)
    except _FormulaError as exc:
        return str(exc)
    except ZeroDivisionError:
        return "#DIV/0!"
    except (SyntaxError, ValueError, TypeError, OverflowError, RecursionError):
        return "#VALUE!"


def _walk(node: ast.AST, grid: _Grid) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str, bool)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _number(_walk(node.operand, grid))
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
        left, right = _number(_walk(node.left, grid)), _number(_walk(node.right, grid))
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        return left ** right
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left, right = _walk(node.left, grid), _walk(node.comparators[0], grid)
        if isinstance(left, (int, float)) or isinstance(right, (int, float)):
            left, right = _number(left), _number(right)
        op = node.ops[0]
        table = {ast.Eq: left == right, ast.NotEq: left != right}
        if type(op) in table:
            return table[type(op)]
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.GtE):
            return left >= right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        name = node.func.id
        if name == "__ref":
            return grid.value(node.args[0].value)
        if name == "__span":
            return grid.span(node.args[0].value, node.args[1].value)
        name = name.upper()
        if name not in _ALLOWED:
            raise _FormulaError("#NAME?")
        if name == "IF":
            test = _walk(node.args[0], grid)
            if isinstance(test, str) and test.startswith("#"):
                return test
            if bool(_number(test) if not isinstance(test, bool) else test):
                return _walk(node.args[1], grid) if len(node.args) > 1 else True
            return _walk(node.args[2], grid) if len(node.args) > 2 else False
        args = [_walk(a, grid) for a in node.args]
        if name == "N":
            return args[0] if isinstance(args[0], (int, float)) and not isinstance(args[0], bool) else 0
        if name == "ISNUMBER":
            return isinstance(args[0], (int, float)) and not isinstance(args[0], bool)
        if name in ("AND", "OR"):
            values = [bool(_number(v)) for v in _flat(args)]
            return all(values) if name == "AND" else any(values)
        if name == "NOT":
            return not bool(_number(args[0]))
        if name == "ROUND":
            return round(_number(args[0]), int(_number(args[1])) if len(args) > 1 else 0)
        if name in ("ABS", "SQRT"):
            value = _number(args[0])
            return abs(value) if name == "ABS" else math.sqrt(value)
        numbers = [_number(v) for v in _flat(args) if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if name == "SUM":
            return sum(numbers)
        if not numbers:
            return "#DIV/0!" if name == "AVERAGE" else 0
        return {"MIN": min, "MAX": max, "AVERAGE": lambda v: sum(v) / len(v)}[name](numbers)
    if isinstance(node, ast.Name) and node.id in ("True", "False"):
        return node.id == "True"
    raise _FormulaError("#VALUE!")


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def _load(data: bytes, suffix: str) -> list[dict]:
    """Every sheet as {name, cells, cached, rows, columns}: cells hold values
    and formulas as written; cached, the values Excel last saved."""
    if suffix in (".csv", ".tsv"):
        text = data.decode("utf-8-sig", errors="replace")
        rows = list(csv.reader(io.StringIO(text), delimiter="\t" if suffix == ".tsv" else ","))
        cells: dict[str, Any] = {}
        for r, row in enumerate(rows, 1):
            for c, raw in enumerate(row, 1):
                value: Any = raw.strip()
                try:
                    value = float(value) if value and re.fullmatch(r"-?\d+(?:\.\d+)?", value) else value
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                except ValueError:
                    pass
                if value != "":
                    cells[f"{_column_letters(c)}{r}"] = value
        width = max((len(r) for r in rows), default=0)
        return [{"name": "Sheet1", "cells": cells, "cached": {}, "rows": len(rows), "columns": width}]

    from openpyxl import load_workbook

    formulas = load_workbook(io.BytesIO(data), data_only=False)
    values = load_workbook(io.BytesIO(data), data_only=True)
    sheets = []
    for ws in formulas.worksheets:
        cached_ws = values[ws.title]
        cells, cached = {}, {}
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                ref = cell.coordinate
                cells[ref] = cell.value
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    cached[ref] = cached_ws[ref].value
        sheets.append({"name": ws.title, "cells": cells, "cached": cached,
                       "rows": ws.max_row, "columns": ws.max_column})
    return sheets


def _render(sheet: dict, max_rows: int, max_columns: int) -> str:
    """A sheet as a markdown table: each column headed by its letter and its
    header text, each row numbered, a formula shown as its value then itself."""
    grid = _Grid(sheet["cells"], sheet["cached"])
    rows = min(sheet["rows"], max_rows)
    columns = min(sheet["columns"], max_columns)
    if not rows or not columns:
        return f'**Sheet "{sheet["name"]}"** is empty.'
    letters = [_column_letters(c) for c in range(1, columns + 1)]
    header = [f"{l} · {_shown(grid.value(f'{l}1'))}".rstrip(" ·") for l in letters]
    lines = [
        f'**Sheet "{sheet["name"]}"** · A1:{letters[-1]}{sheet["rows"]}'
        + (f" (the first {rows} rows shown)" if sheet["rows"] > rows else ""),
        "",
        "| " + " | ".join(header) + " | Row |",
        "|" + "---|" * (len(header) + 1),
    ]
    for r in range(2, rows + 1):
        cells = []
        for l in letters:
            ref = f"{l}{r}"
            raw = sheet["cells"].get(ref)
            if isinstance(raw, str) and raw.startswith("="):
                cells.append(f"{_shown(grid.value(ref))} ({raw.replace('|', '/')})")
            else:
                cells.append(_shown(raw))
        if any(cells):
            lines.append("| " + " | ".join(cells) + f" | {r} |")
    return "\n".join(lines)


class Tools:
    class Valves(BaseModel):
        workspace: str = Field(
            default="",
            description="The folder copies are written to - the same one 4CE Workspace Files uses. Blank uses DATA_DIR/4ce/workspace.",
        )
        max_rows: int = Field(default=200, description="Rows of a sheet read into a conversation.")
        max_columns: int = Field(default=26, description="Columns of a sheet read into a conversation.")

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    def _workspace(self) -> Path:
        root = Path(self.valves.workspace).expanduser() if self.valves.workspace.strip() else _default_workspace()
        root.mkdir(parents=True, exist_ok=True)
        return root

    async def _source(self, file: str, files: list | None) -> tuple[str, bytes, str] | str:
        """(name, bytes, where) of the spreadsheet named - attached to the chat
        or in the workspace - or why it could not be found."""
        wanted = (file or "").strip()
        attached = []
        for item in files or []:
            if not isinstance(item, dict):
                continue
            inner = item.get("file") if isinstance(item.get("file"), dict) else {}
            name = item.get("name") or inner.get("filename") or (inner.get("meta") or {}).get("name") or ""
            if name.lower().endswith(SHEET_TYPES):
                attached.append((name, item.get("id") or inner.get("id")))
        pick = next((a for a in attached if a[0].lower() == wanted.lower()), None)
        if pick is None and not wanted and attached:
            pick = attached[0]
        if pick and pick[1]:
            try:
                from open_webui.models.files import Files
                from open_webui.storage.provider import Storage

                record = await Files.get_file_by_id(pick[1])
                local = await asyncio.to_thread(Storage.get_file, record.path)
                return pick[0], await asyncio.to_thread(Path(local).read_bytes), "attached to the chat"
            except Exception as exc:
                return f"`{pick[0]}` is attached but could not be read: {exc}"
        target = _inside(self._workspace(), wanted) if wanted else None
        if target is None:
            return (f"`{wanted}` is outside the workspace." if wanted
                    else "No spreadsheet is attached, and none was named.")
        if not target.is_file():
            return f"`{wanted}` is not in the workspace, and no attached spreadsheet has that name."
        if target.suffix.lower() not in SHEET_TYPES:
            return f"`{wanted}` is not a spreadsheet 4CE reads ({', '.join(SHEET_TYPES)})."
        rel = target.relative_to(self._workspace().resolve()).as_posix()
        return rel, await asyncio.to_thread(target.read_bytes), "workspace"

    async def read_sheet(
        self,
        file: str = "",
        sheet: str = "",
        __files__: list | None = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Read an Excel workbook or a CSV as tables, with every cell's reference and every formula.

        Use this when a request attaches a spreadsheet, or names one in the workspace, and asks
        anything about its contents.

        :param file: The file's name as attached, or its path in the workspace. Blank reads the one attached spreadsheet.
        :param sheet: One sheet to read. Blank reads them all.
        :return: Each sheet as a markdown table - columns headed "B · Previous (mm)", rows numbered, formulas shown as "value (=formula)" - or why it could not be read.
        """
        found = await self._source(file, __files__)
        if isinstance(found, str):
            return found
        name, data, where = found
        await _emit(__event_emitter__, "sheet", f"TOOL: reading {name}")
        try:
            sheets = await asyncio.to_thread(_load, data, Path(name).suffix.lower())
        except Exception as exc:
            return f"`{name}` could not be read as a spreadsheet: {exc}"
        chosen = [s for s in sheets if not sheet or s["name"].lower() == sheet.lower()]
        if not chosen:
            return f'`{name}` has no sheet "{sheet}". Its sheets: ' + ", ".join(s["name"] for s in sheets) + "."
        entry = _logged("sheet.read", tool="read_sheet", file=name, source=where,
                        sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
                        sheets=[s["name"] for s in chosen])
        formulas = sum(1 for s in chosen for v in s["cells"].values() if isinstance(v, str) and v.startswith("="))
        await _emit(__event_emitter__, "sheet", f"Read {name}", done=True)
        return (
            f"`{name}` ({where}) - {len(sheets)} sheet{'s' if len(sheets) != 1 else ''}"
            + (f", {formulas} formula{'s' if formulas != 1 else ''}" if formulas else "")
            + (f", audit trail entry {entry['seq']}" if entry else "")
            + ".\n\n"
            + "\n\n".join(_render(s, self.valves.max_rows, self.valves.max_columns) for s in chosen)
        )

    async def write_sheet(
        self,
        changes: str,
        file: str = "",
        sheet: str = "",
        save_as: str = "",
        __user__: dict | None = None,
        __files__: list | None = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
        __preview__: bool = False,
    ) -> str:
        """
        Write changes to a copy of an Excel workbook or a CSV - never the file itself - keeping every formula live.

        :param changes: A JSON list. Each item is one of: {"column": "Corrosion rate (mm/yr)", "formula": "=(B{row}-C{row})/E{row}"} to add a column, the formula written into every data row with {row} its row number; {"column": "Interval (yr)", "values": [0.5, 2, ...]} to add a column of values, one per data row from row 2; {"cell": "G2", "formula": "=B2-C2"}; or {"cell": "G2", "value": 12.5}.
        :param file: The spreadsheet, as attached or its path in the workspace. Blank uses the one attached spreadsheet.
        :param sheet: The sheet to change. Blank uses the first.
        :param save_as: Where to write the copy in the workspace, ending .xlsx. Blank writes "<name> - 4CE.xlsx".
        :return: A download link to the copy and what its new cells evaluate to, or why nothing was written.
        """
        try:
            parsed = json.loads(changes) if isinstance(changes, str) else changes
        except ValueError as exc:
            return f"The changes are not valid JSON ({exc}); nothing was written."
        if isinstance(parsed, dict):
            parsed = parsed.get("changes", [parsed])
        if not isinstance(parsed, list) or not parsed:
            return "No changes were given; nothing was written."
        for change in parsed:
            if not isinstance(change, dict) or not (
                ("column" in change or "cell" in change)
                and ("formula" in change or "value" in change or ("values" in change and "column" in change))
            ):
                return f"A change must name a column or a cell, and a formula or a value: {change}. Nothing was written."
            formula = change.get("formula")
            if formula is not None:
                if not str(formula).startswith("="):
                    return f"`{formula}` is not a formula (it must start with =). Nothing was written."
                if _UNSAFE.search(str(formula)):
                    return (f"`{formula}` could reach outside the workbook - another file, a web service, "
                            "a link or a program - so it was refused. Nothing was written.")
            if "cell" in change and not _REF.fullmatch(str(change["cell"]).upper()):
                return f"`{change['cell']}` is not a cell reference. Nothing was written."

        found = await self._source(file, __files__)
        if isinstance(found, str):
            return found
        name, data, where = found
        root = self._workspace()
        target_name = save_as.strip() or f"{Path(name).stem} - 4CE.xlsx"
        if not target_name.lower().endswith(".xlsx"):
            target_name = str(Path(target_name).with_suffix(".xlsx"))
        target = _inside(root, target_name)
        if target is None or VERSIONS in target.relative_to(root.resolve()).parts:
            return f"`{target_name}` is outside the workspace; nothing was written."
        if where == "workspace" and target == _inside(root, name):
            return "The copy would overwrite the source, which 4CE never changes. Name another file."

        if not __preview__:
            await _emit(__event_emitter__, "sheet", f"TOOL: writing a copy of {name}")
        try:
            payload, notes, preview = await asyncio.to_thread(_apply, data, Path(name).suffix.lower(), sheet, parsed)
        except _Refused as exc:
            return f"{exc} Nothing was written."
        except Exception as exc:
            return f"`{name}` could not be changed: {exc}. Nothing was written."
        if __preview__:
            # What approval would write, for the reviewer to approve: built in
            # memory, evaluated, and not written anywhere.
            return (
                f"On approval, 4CE writes a copy of `{name}` as `{target.relative_to(root.resolve()).as_posix()}` "
                "in the workspace; the file itself is not changed.\n\n"
                + "\n".join(f"- {n}" for n in notes)
                + ("\n\nWhat the new cells will give, as Excel calculates them:\n\n" + preview if preview else "")
            )

        kept = None
        if target.exists():
            history = root.resolve() / VERSIONS / target.relative_to(root.resolve())
            history.mkdir(parents=True, exist_ok=True)
            number = len(list(history.glob(f"{target.stem}.v*{target.suffix}"))) + 1
            kept = history / f"{target.stem}.v{number}{target.suffix}"
            await asyncio.to_thread(kept.write_bytes, target.read_bytes())
        target.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, payload)
        relative = target.relative_to(root.resolve()).as_posix()

        link = ""
        if __user__ and __user__.get("id"):
            link = await _register(__user__["id"], payload, target.name)
        entry = _logged(
            "file.write", tool="write_sheet", file=relative, source=name,
            source_sha256=hashlib.sha256(data).hexdigest(), sha256=hashlib.sha256(payload).hexdigest(),
            bytes=len(payload), changes=hashlib.sha256(json.dumps(parsed, sort_keys=True).encode()).hexdigest(),
            kept=kept.relative_to(root.resolve()).as_posix() if kept else None,
        )
        await _emit(__event_emitter__, "sheet", f"Wrote {target.name}", done=True)
        return (
            f"**Excel workbook** · {target.stem} · {max(1, len(payload) // 1024)} KB, stored on this machine"
            + (f" · [Download .xlsx]({link})" if link else "")
            + f"\n\nWritten to `{relative}` in the workspace"
            + (f"; the earlier copy kept as `{kept.relative_to(root.resolve()).as_posix()}`" if kept else "")
            + f". The source, `{name}`, was not changed"
            + (f"; audit trail entry {entry['seq']}" if entry else "")
            + ".\n\n" + "\n".join(f"- {n}" for n in notes)
            + ("\n\nWhat the new cells give, as Excel will calculate them:\n\n" + preview if preview else "")
        )


class _Refused(Exception):
    pass


def _apply(data: bytes, suffix: str, sheet: str, changes: list[dict]) -> tuple[bytes, list[str], str]:
    """The changes applied to a copy: the workbook itself, or a new one built
    from a CSV. Returns the copy, what was done, and the new cells' values."""
    from copy import copy

    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font

    notes: list[str] = []
    if suffix in (".csv", ".tsv"):
        book = Workbook()
        ws = book.active
        ws.title = "Sheet1"
        for ref, value in _load(data, suffix)[0]["cells"].items():
            ws[ref] = value
        for cell in ws[1]:
            cell.font = Font(bold=True)
        notes.append("The CSV was copied into a workbook, so its formulas can stay live.")
    else:
        book = load_workbook(io.BytesIO(data))
        ws = book[sheet] if sheet and sheet in book.sheetnames else book.worksheets[0]
        if sheet and sheet not in book.sheetnames:
            raise _Refused(f'There is no sheet "{sheet}".')

    # Data rows: below the header, down to the last row with anything in column A.
    last = max((c.row for c in ws["A"] if c.value not in (None, "")), default=1)
    written: list[str] = []
    for change in changes:
        if "column" in change:
            header = str(change["column"]).strip() or "New column"
            column = ws.max_column + 1
            letters = _column_letters(column)
            ws.cell(row=1, column=column, value=header)
            model = ws.cell(row=1, column=column - 1)
            ws.cell(row=1, column=column).font = copy(model.font)
            ws.cell(row=1, column=column).fill = copy(model.fill)
            ws.cell(row=1, column=column).alignment = copy(model.alignment)
            ws.column_dimensions[letters].width = max(12, min(40, len(header) + 2))
            given = change.get("values") if isinstance(change.get("values"), list) else None
            for r in range(2, last + 1):
                if "formula" in change:
                    ws.cell(row=r, column=column, value=str(change["formula"]).replace("{row}", str(r)))
                elif given is not None:
                    value = given[r - 2] if r - 2 < len(given) else None
                    ws.cell(row=r, column=column, value=None if value in ("", None) else value)
                else:
                    ws.cell(row=r, column=column, value=change["value"])
                written.append(f"{letters}{r}")
            what = (f"`{change['formula']}`" if "formula" in change
                    else "the values given, row by row" if given is not None else f"{change['value']!r}")
            notes.append(f"Added column {letters}, \"{header}\", as {what} on rows 2-{last}.")
        else:
            ref = str(change["cell"]).upper().replace("$", "")
            ws[ref] = change["formula"] if "formula" in change else change["value"]
            written.append(ref)
            what = f"`{change['formula']}`" if "formula" in change else f"{change['value']!r}"
            notes.append(f"Set {ref} to {what}.")

    buffer = io.BytesIO()
    book.save(buffer)
    payload = buffer.getvalue()

    # What the new cells evaluate to: the copy, read back, through the same
    # evaluator read_sheet uses.
    copied = _load(payload, ".xlsx")
    sheet_data = next(s for s in copied if s["name"] == ws.title)
    grid = _Grid(sheet_data["cells"])
    columns = sorted({re.match(r"[A-Z]+", ref).group(0) for ref in written}, key=_column_number)
    label = next((l for l in ("A",) if l not in columns), None)
    head = ([f"{label} · {_shown(grid.value(label + '1'))}"] if label else []) + [
        f"{c} · {_shown(grid.value(c + '1'))}" for c in columns
    ]
    lines = ["| " + " | ".join(head) + " | Row |", "|" + "---|" * (len(head) + 1)]
    rows = sorted({int(re.search(r"\d+", ref).group(0)) for ref in written} - {1})
    for r in rows:
        cells = ([_shown(grid.value(f"{label}{r}"))] if label else []) + [_shown(grid.value(f"{c}{r}")) for c in columns]
        lines.append("| " + " | ".join(cells) + f" | {r} |")
    blocked = [ref for ref in written if grid.value(ref) == "#BLOCKED!"]
    if blocked:
        raise _Refused(f"{', '.join(blocked)} would reach outside the workbook.")
    return payload, notes, "\n".join(lines) if len(lines) > 2 else ""


async def _register(user_id: str, payload: bytes, filename: str) -> str:
    """The copy registered for download, as the other tools register theirs."""
    try:
        from open_webui.models.files import FileForm, Files
        from open_webui.storage.provider import Storage

        file_id = str(uuid.uuid4())
        contents, path = await asyncio.to_thread(Storage.upload_file, io.BytesIO(payload), f"{file_id}_{filename}", {})
        record = await Files.insert_new_file(
            user_id,
            FileForm(
                id=file_id, filename=filename, path=path, data={},
                meta={"name": filename, "size": len(contents),
                      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
            ),
        )
        return f"/api/v1/files/{file_id}/content" if record else ""
    except Exception:
        return ""


async def _emit(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})
