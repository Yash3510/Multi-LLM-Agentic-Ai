"""4CE: watch what the workbench actually connects to.

The sovereignty audit reads configuration. It can establish that no external
endpoint is configured, which is assurance: necessary, not sufficient. This
module observes instead. It samples the operating system's socket table a few
times a second, keeps the processes that make up the workbench, and sorts every
connection they hold by where it goes - this machine, the local network, or
anywhere else - so "nothing leaves the premises" becomes a count you can watch
not climbing.

What is in scope is stated rather than implied:

- the backend: this process, the launcher that started it, and whatever it
  spawns - the docker CLI during a sandbox run, for one;
- each model server the configuration points at on this machine, found by the
  port it listens on, with the family of processes around it;
- the frontend dev server, when one is running.

What it cannot see is stated too, here and on the page: a connection that
opens and closes between two samples; DNS lookups, which the operating
system's resolver makes on a process's behalf; and anything outside that
scope - the browser, the operating system, other programs. A capture on the
uplink closes those gaps. This is the part the workbench can show about
itself, continuously, while it works.
"""

import asyncio
import errno
import ipaddress
import logging
import os
import threading
import time
from urllib.parse import urlparse

import psutil

log = logging.getLogger(__name__)

SAMPLE_SECONDS = float(os.environ.get("FOURCE_EGRESS_SAMPLE_SECONDS", "0.25"))
SCOPE_REFRESH_SECONDS = 5.0
FRONTEND_PORT = int(os.environ.get("FOURCE_FRONTEND_PORT", "5173"))
# A literal address, so the canary makes its attempt without a DNS lookup.
CANARY_TARGET = os.environ.get("FOURCE_CANARY_TARGET", "1.1.1.1:443")
CANARY_TIMEOUT = 3.0
# A flow not seen for this long is forgotten, so a reused port counts again.
FLOW_MEMORY_SECONDS = 600
EVENT_LIMIT = 200
LIVE_LIMIT = 60

LIMITS = (
    f"Sampled every {int(SAMPLE_SECONDS * 1000)} ms. A connection that opens and closes "
    "between two samples can be missed; a packet capture on the uplink closes that gap.",
    "DNS lookups are made by the operating system's resolver on a process's behalf, so "
    "they do not appear among the workbench's own connections.",
    "Scope is the backend, the model server and the frontend, with their child processes - "
    "except a web browser one of them opened, which is the person's own browsing. The "
    "operating system and other programs are outside it too.",
    "Sandbox containers run with --network none, so they have no interface to connect with.",
)

# Windows reports a firewall refusal as WSAEACCES, an unplugged uplink as
# WSAENETUNREACH or WSAEHOSTUNREACH; POSIX has its own numbers for the same.
_DENIED = {errno.EACCES, errno.EPERM, 10013}
_NO_ROUTE = {errno.ENETUNREACH, errno.EHOSTUNREACH, 10051, 10065}


def classify(ip: str) -> str:
    """'local', 'lan' or 'external' for a remote address."""
    try:
        address = ipaddress.ip_address(str(ip).split("%", 1)[0])
    except ValueError:
        return "external"
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    if address.is_loopback or address.is_unspecified:
        return "local"
    if address.is_private or address.is_link_local or address.is_multicast:
        return "lan"
    return "external"


# A web browser opened from a model server's window - a link clicked in its
# UI - is the person's browsing, not the workbench's. Counted as a descendant,
# its tabs' connections to GitHub and Google were charged to the model server.
BROWSERS = frozenset({
    "brave.exe", "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "vivaldi.exe",
    "iexplore.exe", "arc.exe", "brave", "brave browser", "chrome", "chromium",
    "google chrome", "firefox", "opera", "vivaldi", "safari", "microsoft edge",
})


def _descendants(process, excluded: dict | None = None) -> list:
    """Every descendant, less any browser and what that browser started.
    A browser left out is noted in `excluded`, so the page can say so."""
    found = []
    try:
        children = process.children()
    except psutil.Error:
        return found
    for child in children:
        try:
            name = child.name()
        except psutil.Error:
            continue
        if name.lower() in BROWSERS:
            if excluded is not None:
                excluded[child.pid] = name
            continue
        found.append(child)
        found.extend(_descendants(child, excluded))
    return found


def _family(pid: int, excluded: dict | None = None) -> dict[int, tuple[str, str]]:
    """A process, the same-program ancestors that launched it, and every descendant.

    Climbing matters on Windows, where a virtual environment's python.exe is a
    launcher that starts the real interpreter as its child, and for model
    servers, which serve from one process of an application made of several.
    """
    try:
        root = psutil.Process(pid)
        name = root.name()
        while True:
            parent = root.parent()
            if parent is None or parent.name() != name:
                break
            root = parent
        members = [root, *_descendants(root, excluded)]
    except psutil.Error:
        return {}
    family = {}
    for member in members:
        try:
            name = member.name()
        except psutil.Error:
            continue
        try:
            # The file a firewall rule has to name. For a venv on Windows this
            # is the base interpreter, not the launcher in .venv\Scripts.
            exe = member.exe()
        except psutil.Error:
            exe = ""
        family[member.pid] = (name, exe)
    return family


def _endpoint(address) -> str:
    if not address:
        return ""
    host = address.ip if ":" not in address.ip else f"[{address.ip}]"
    return f"{host}:{address.port}"


class EgressWatch:
    def __init__(self):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._per_process = False
        self._model_ports: set[int] = set()
        self._expected: set[tuple[str, int]] = set()
        self._scope: dict[int, dict] = {}
        self._excluded: dict[int, dict] = {}
        self._scope_at = 0.0
        self.generation = 0
        self._clear()

    def _clear(self) -> None:
        self.since = time.time()
        self.samples = 0
        self.last_sample = 0.0
        self.error = ""
        self.flows = {
            "local": 0, "lan_in": 0, "lan_expected": 0, "lan_out": 0,
            "external": 0, "canary": 0,
        }
        self._seen: dict[tuple, float] = {}
        self._events: dict[str, dict[tuple, dict]] = {"external": {}, "lan_out": {}}
        self._live: list[dict] = []
        self.canaries: list[dict] = []
        self._canary: tuple[str, int, float] | None = None

    # -- lifecycle ---------------------------------------------------------

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="4ce-egress-watch", daemon=True)
        self._thread.start()
        log.info("4CE egress watch started, sampling every %.0f ms", SAMPLE_SECONDS * 1000)

    def stop(self) -> None:
        self._stop.set()

    def reset(self) -> None:
        """Open a fresh observation window - at the start of a demo, say."""
        with self._lock:
            self.generation += 1
            self._clear()

    def set_endpoints(self, urls: list[str]) -> None:
        """Take the configured model and embedding endpoints.

        One on this machine puts the process listening on its port in scope.
        One elsewhere on the LAN, given as an address, is an expected
        destination: the backend reaching an on-premise GPU server is the
        design, not a leak, and is counted apart from other LAN traffic.
        """
        ports, expected = set(), set()
        for url in urls:
            if not url or not str(url).strip():
                continue
            parsed = urlparse(url if "://" in url else f"http://{url}")
            host = (parsed.hostname or "").lower()
            try:
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
            except ValueError:
                continue
            if host in ("localhost", "host.docker.internal") or classify(host) == "local":
                ports.add(port)
            elif classify(host) == "lan":
                expected.add((host, port))
        with self._lock:
            changed = ports != self._model_ports
            self._model_ports, self._expected = ports, expected
            if changed:
                self._scope_at = 0.0

    # -- sampling ----------------------------------------------------------

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                self._sample()
            except Exception as exc:  # keep watching; say what went wrong
                with self._lock:
                    self.error = f"{type(exc).__name__}: {exc}"
                log.debug("4CE egress sample failed", exc_info=True)
            self._stop.wait(max(0.0, SAMPLE_SECONDS - (time.monotonic() - started)))

    def _listeners(self) -> dict[int, set[int]]:
        """Listening port -> the pids listening on it."""
        ports: dict[int, set[int]] = {}
        if not self._per_process:
            try:
                for conn in psutil.net_connections(kind="inet"):
                    if conn.status == psutil.CONN_LISTEN and conn.laddr and conn.pid:
                        ports.setdefault(conn.laddr.port, set()).add(conn.pid)
                return ports
            except psutil.AccessDenied:
                # macOS lists other processes' sockets only for root. Asking
                # each process works for the ones this user owns.
                self._per_process = True
        for process in psutil.process_iter():
            try:
                for conn in process.net_connections(kind="inet"):
                    if conn.status == psutil.CONN_LISTEN and conn.laddr:
                        ports.setdefault(conn.laddr.port, set()).add(process.pid)
            except psutil.Error:
                continue
        return ports

    def _refresh_scope(self) -> None:
        listeners = self._listeners()
        listening: dict[int, set[int]] = {}
        for port, pids in listeners.items():
            for pid in pids:
                listening.setdefault(pid, set()).add(port)

        with self._lock:
            model_ports = set(self._model_ports)
        scope: dict[int, dict] = {}
        excluded: dict[int, dict] = {}

        def add(pids, role: str) -> None:
            for pid in pids:
                left_out: dict[int, str] = {}
                for member, (name, exe) in _family(pid, left_out).items():
                    scope.setdefault(member, {
                        "name": name, "exe": exe, "role": role,
                        "listening": listening.get(member, set()),
                    })
                for member, name in left_out.items():
                    excluded.setdefault(member, {"name": name, "role": role})

        add([os.getpid()], "backend")
        for port in sorted(model_ports):
            add(listeners.get(port, ()), "model server")
        add(listeners.get(FRONTEND_PORT, ()), "frontend")

        with self._lock:
            self._scope = scope
            self._excluded = excluded
            self._scope_at = time.time()

    def _connections(self, pids) -> list[tuple[int, object]]:
        if not self._per_process:
            try:
                return [(c.pid, c) for c in psutil.net_connections(kind="inet") if c.pid]
            except psutil.AccessDenied:
                self._per_process = True
        found = []
        for pid in pids:
            try:
                found.extend((pid, c) for c in psutil.Process(pid).net_connections(kind="inet"))
            except psutil.Error:
                continue
        return found

    def _sample(self) -> None:
        now = time.time()
        if now - self._scope_at >= SCOPE_REFRESH_SECONDS:
            self._refresh_scope()
        with self._lock:
            scope, expected, canary = self._scope, self._expected, self._canary

        observed = []
        for pid, conn in self._connections(list(scope)):
            member = scope.get(pid)
            if member is None or not conn.raddr:
                continue
            inbound = bool(conn.laddr) and conn.laddr.port in member["listening"]
            kind = classify(conn.raddr.ip)
            if kind == "lan":
                if inbound:
                    kind = "lan_in"
                elif (conn.raddr.ip, conn.raddr.port) in expected:
                    kind = "lan_expected"
                else:
                    kind = "lan_out"
            elif (
                kind == "external"
                and canary
                and member["role"] == "backend"
                and (conn.raddr.ip, conn.raddr.port) == canary[:2]
                and now <= canary[2]
            ):
                kind = "canary"
            observed.append((pid, member, conn, kind, inbound))

        with self._lock:
            self.samples += 1
            self.last_sample = now
            live = []
            for pid, member, conn, kind, inbound in observed:
                key = (pid, _endpoint(conn.laddr), _endpoint(conn.raddr))
                fresh = key not in self._seen
                self._seen[key] = now
                if fresh:
                    self.flows[kind] += 1
                if kind in self._events:
                    self._note(kind, pid, member, conn, inbound, now, fresh)
                if len(live) < LIVE_LIMIT:
                    live.append({
                        "process": member["name"], "pid": pid, "role": member["role"],
                        "local": _endpoint(conn.laddr), "remote": _endpoint(conn.raddr),
                        "state": conn.status, "kind": kind,
                        "direction": "in" if inbound else "out",
                    })
            self._live = live
            if len(self._seen) > 5000 or self.samples % 240 == 0:
                stale = now - FLOW_MEMORY_SECONDS
                self._seen = {k: t for k, t in self._seen.items() if t >= stale}
            self.error = ""

    def _note(self, kind, pid, member, conn, inbound, now, fresh) -> None:
        events = self._events[kind]
        key = (pid, conn.raddr.ip, conn.raddr.port)
        event = events.get(key)
        if event is None:
            if len(events) >= EVENT_LIMIT:
                return
            event = events[key] = {
                "first": now, "last": now, "process": member["name"], "pid": pid,
                "role": member["role"], "remote": _endpoint(conn.raddr),
                "direction": "in" if inbound else "out", "state": conn.status, "flows": 0,
            }
        event["last"] = now
        event["state"] = conn.status
        if fresh:
            event["flows"] += 1

    # -- the canary --------------------------------------------------------

    async def run_canary(self) -> dict:
        """Try to reach a public address from the backend, and say what happened.

        Only a TCP handshake: nothing is sent, and the socket is closed as soon
        as it opens. The attempt is the point - blocked is the result a
        sovereign deployment should show, and reachable is reported plainly,
        because it means nothing on this host stops a connection even though
        the workbench did not make one.
        """
        host, _, port = CANARY_TARGET.rpartition(":")
        host, port = host.strip("[]"), int(port)
        with self._lock:
            self._canary = (host, port, time.time() + CANARY_TIMEOUT + 2)
        started = time.monotonic()
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), CANARY_TIMEOUT)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            outcome = "reachable"
            detail = (
                "the connection opened. The workbench made no such call, but nothing on "
                "this host prevents one - add an egress rule to make that physical"
            )
        except asyncio.TimeoutError:
            outcome = "blocked"
            detail = f"no answer within {CANARY_TIMEOUT:.0f} s - dropped by a firewall, or no route out"
        except ConnectionRefusedError:
            outcome, detail = "blocked", "refused on the way out"
        except OSError as exc:
            code = getattr(exc, "winerror", None) or exc.errno
            if code in _DENIED or isinstance(exc, PermissionError):
                outcome, detail = "blocked", "denied by the host firewall"
            elif code in _NO_ROUTE:
                outcome, detail = "blocked", "no route to the internet - the uplink is down or disconnected"
            else:
                outcome, detail = "blocked", f"failed: {exc.strerror or exc}"
        record = {
            "at": time.time(), "target": CANARY_TARGET, "outcome": outcome, "detail": detail,
            "ms": round((time.monotonic() - started) * 1000),
        }
        with self._lock:
            self.canaries.insert(0, record)
            del self.canaries[20:]
        log.info("4CE canary to %s: %s (%s)", CANARY_TARGET, outcome, detail)
        return record

    # -- reading -----------------------------------------------------------

    def snapshot(self) -> dict:
        with self._lock:
            scope = [
                {"pid": pid, "process": m["name"], "exe": m.get("exe", ""), "role": m["role"],
                 "listening": sorted(m["listening"])}
                for pid, m in sorted(self._scope.items(), key=lambda i: (i[1]["role"], i[0]))
            ]
            return {
                "running": self.running,
                "generation": self.generation,
                "since": self.since,
                "now": time.time(),
                "samples": self.samples,
                "interval_ms": int(SAMPLE_SECONDS * 1000),
                "last_sample": self.last_sample,
                "error": self.error,
                "mode": "per-process" if self._per_process else "system table",
                "flows": dict(self.flows),
                "external": sorted(self._events["external"].values(), key=lambda e: -e["last"]),
                "lan_out": sorted(self._events["lan_out"].values(), key=lambda e: -e["last"]),
                "scope": scope,
                "excluded": [
                    {"pid": pid, "process": m["name"], "role": m["role"]}
                    for pid, m in sorted(self._excluded.items())
                ],
                "live": list(self._live),
                "canaries": list(self.canaries),
                "canary_target": CANARY_TARGET,
                "expected_lan": sorted(f"{h}:{p}" for h, p in self._expected),
                "limits": list(LIMITS),
            }

    def mark(self) -> dict:
        """Where the counters stand now, to compare a run's end against."""
        with self._lock:
            return {
                "generation": self.generation, "samples": self.samples,
                "external": self.flows["external"], "lan_out": self.flows["lan_out"],
            }

    def since_mark(self, mark: dict | None) -> dict:
        """What was observed between a mark and now: the evidence for one run.

        'observed' is False unless the watch was running and sampled in
        between. A run nobody watched gets no number rather than a zero.
        """
        with self._lock:
            if not mark or not self.running:
                return {"observed": False, "reason": "the egress watch is not running"}
            # A window reset mid-run: everything in the new window is this run's.
            base = mark if self.generation == mark.get("generation") else {
                "samples": 0, "external": 0, "lan_out": 0,
            }
            samples = self.samples - base["samples"]
            if samples <= 0:
                return {"observed": False, "reason": "no samples were taken during the run"}
            return {
                "observed": True,
                "external": self.flows["external"] - base["external"],
                "lan_out": self.flows["lan_out"] - base["lan_out"],
                "samples": samples,
                "processes": len(self._scope),
                "interval_ms": int(SAMPLE_SECONDS * 1000),
            }


watch = EgressWatch()


async def keep_endpoints_current(get_config, interval: float = 30.0) -> None:
    """Point the watch at the configured model endpoints, and follow changes."""
    keys = ("openai.api_base_urls", "ollama.base_urls",
            "rag.openai.api_base_url", "rag.ollama.base_url")
    while True:
        urls: list[str] = []
        for key in keys:
            try:
                value = await get_config(key)
            except Exception:
                value = None
            if isinstance(value, str):
                urls.append(value)
            elif isinstance(value, (list, tuple)):
                urls.extend(str(v) for v in value)
        watch.set_endpoints(urls)
        await asyncio.sleep(interval)
