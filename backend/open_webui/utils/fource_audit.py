"""
4CE's audit trail: an append-only, hash-chained record of what the workbench
did - each request, the sources it drew on, every model call and tool call with
the SHA-256 of what went in and what came out, every file written, the verdict,
who approved and what was released.

Each entry carries the hash of the entry before it, and its own hash covers its
content and that link. Changing, removing or reordering any entry breaks the
chain from that point, and verify() names the first entry that no longer
matches. That makes the trail tamper-evident, not tamper-proof: anyone who can
write the file can rewrite the whole chain after it. So the head hash is shown
wherever the trail is - copy it somewhere they cannot reach, such as a printed
report, and it pins everything up to that point.

One JSON object per line in DATA_DIR/4ce/audit.jsonl. An entry holds names,
counts and hashes - never the text of a prompt, a document or an answer - so
the trail does not become a second copy of what it records. The hash of a
released answer is its fingerprint: the receipt, the provenance and the Word
report print the same one, so a copy can be matched to its entry here.

Writing an entry never fails the work it records. A failure to write is kept
and reported beside the trail, so a gap is visible rather than silent.
"""

import contextvars
import hashlib
import json
import logging
import os
import threading
import time
from pathlib import Path

log = logging.getLogger(__name__)

GENESIS = "0" * 64

# Who and what an entry belongs to - the chat, the message being answered and
# the requester - bound once when a run starts. A tool called during that run
# records under it without being told: context variables follow an await.
_run: contextvars.ContextVar[dict] = contextvars.ContextVar("fource_audit_run", default={})


def digest(value) -> str:
    """SHA-256 of text, bytes, or anything JSON can say."""
    if isinstance(value, bytes):
        data = value
    elif isinstance(value, str):
        data = value.encode("utf-8")
    else:
        data = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _canonical(entry: dict) -> bytes:
    return json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")


def _seal(entry: dict) -> str:
    return hashlib.sha256(_canonical({k: v for k, v in entry.items() if k != "hash"})).hexdigest()


class AuditTrail:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._seq: int | None = None
        self._head = GENESIS
        self.last_error = ""
        self.failed_writes = 0

    # -- writing -----------------------------------------------------------

    def _load_head(self) -> None:
        seq, head = 0, GENESIS
        last = self._last_line()
        if last:
            entry = json.loads(last)
            seq, head = int(entry["seq"]), str(entry["hash"])
        self._seq, self._head = seq, head

    def _last_line(self) -> bytes:
        if not self.path.exists():
            return b""
        with self.path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            end = handle.tell()
            block, data = 4096, b""
            while end > 0:
                start = max(0, end - block)
                handle.seek(start)
                data = handle.read(end - start) + data
                lines = [line for line in data.split(b"\n") if line.strip()]
                if len(lines) > 1 or start == 0:
                    return lines[-1] if lines else b""
                end = start
        return b""

    def append(self, action: str, **fields) -> dict | None:
        """Add one entry, linked to the one before it. None if it could not
        be written; the reason is kept in last_error."""
        context = _run.get()
        with self._lock:
            try:
                if self._seq is None:
                    self._load_head()
                entry = {
                    "seq": self._seq + 1,
                    "at": round(time.time(), 3),
                    "action": action,
                    **{k: v for k, v in context.items() if v not in (None, "")},
                    **{k: v for k, v in fields.items() if v not in (None, "", [], {})},
                    "prev": self._head,
                }
                entry["hash"] = _seal(entry)
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("ab") as handle:
                    handle.write(_canonical(entry) + b"\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                self._seq, self._head = entry["seq"], entry["hash"]
                return entry
            except Exception as exc:
                self.failed_writes += 1
                self.last_error = f"{type(exc).__name__}: {exc}"
                log.warning("4CE audit trail: could not record %s: %s", action, self.last_error)
                # Re-read the head next time: the file may have moved on.
                self._seq = None
                return None

    # -- reading -----------------------------------------------------------

    def entries(self, after: int = 0, limit: int = 100) -> list[dict]:
        """The entries after a sequence number, newest last, at most `limit`."""
        if not self.path.exists():
            return []
        found: list[dict] = []
        with self.path.open("rb") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if int(entry.get("seq", 0)) > after:
                    found.append(entry)
        return found[-limit:] if limit else found

    def verify(self) -> dict:
        """Walk the whole trail: every entry's hash must cover its content and
        name the entry before it. Reports the first entry that does not."""
        result = {"ok": True, "entries": 0, "head": GENESIS, "broken_at": None, "reason": ""}
        if not self.path.exists():
            return result
        prev, expected = GENESIS, 1
        with self.path.open("rb") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    return {**result, "ok": False, "broken_at": expected, "reason": f"line {number} is not JSON"}
                seq = entry.get("seq")
                if seq != expected:
                    reason = f"entry {expected} is missing" if isinstance(seq, int) and seq > expected else f"entry {seq} is out of order"
                    return {**result, "ok": False, "broken_at": expected, "reason": reason}
                if entry.get("prev") != prev:
                    return {**result, "ok": False, "broken_at": seq, "reason": f"entry {seq} does not follow entry {seq - 1}"}
                if entry.get("hash") != _seal(entry):
                    return {**result, "ok": False, "broken_at": seq, "reason": f"entry {seq} was changed after it was written"}
                prev, expected = entry["hash"], expected + 1
                result.update(entries=seq, head=prev)
        return result

    def status(self) -> dict:
        """Where the trail is, how long, its head, and any write that failed."""
        with self._lock:
            if self._seq is None:
                try:
                    self._load_head()
                except Exception as exc:
                    self.last_error = f"{type(exc).__name__}: {exc}"
            return {
                "path": str(self.path),
                "count": self._seq or 0,
                "head": self._head,
                "last_error": self.last_error,
                "failed_writes": self.failed_writes,
            }


def _default_path() -> Path:
    try:
        from open_webui.env import DATA_DIR

        return Path(DATA_DIR) / "4ce" / "audit.jsonl"
    except Exception:
        return Path("data") / "4ce" / "audit.jsonl"


trail = AuditTrail(Path(os.environ.get("FOURCE_AUDIT_PATH") or _default_path()))


def bind(**context) -> contextvars.Token:
    """Name the run the following entries belong to: chat, message, user."""
    return _run.set({k: v for k, v in context.items() if v})


def record(action: str, **fields) -> dict | None:
    """Add an entry to the trail. Never raises."""
    try:
        return trail.append(action, **fields)
    except Exception:
        return None
