import hashlib
import json
import logging
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from botocore.exceptions import ClientError
from botocore.loaders import Loader

from fource.storage import make_s3_client

BODY = b"x" * 1000
KEY = "0190a0b1000070008000000000000001/0190a0b10000700080000000000000ff"


class _FakeS3(BaseHTTPRequestHandler):
    """Just enough S3 to see where requests go and what they carry. The first GET answers
    that the bucket lives in another region, as S3 does, so the client's redirect shows."""

    seen: list[tuple[str, str, dict[str, str]]] = []
    gets = 0

    def log_message(self, format: str, *args: object) -> None:
        return None

    def _record(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        headers = {name.lower(): value for name, value in self.headers.items()}
        _FakeS3.seen.append((self.command, self.path, headers))

    def _answer(self, status: int, body: bytes = b"") -> None:
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("ETag", '"0"')
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self) -> None:
        self._record()
        self._answer(503 if self.path.endswith("/busy") else 200)

    def do_PUT(self) -> None:
        self._record()
        self._answer(200)

    def do_GET(self) -> None:
        self._record()
        _FakeS3.gets += 1
        if _FakeS3.gets == 1:
            self._answer(
                400,
                b"<Error><Code>AuthorizationHeaderMalformed</Code><Message>m</Message>"
                b"<Region>eu-west-1</Region></Error>",
            )
        else:
            self._answer(200, BODY)


@pytest.fixture
def fake_s3() -> Iterator[str]:
    _FakeS3.seen, _FakeS3.gets = [], 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeS3)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.fixture
def listeners() -> Iterator[tuple[socket.socket, socket.socket]]:
    """A TCP socket posing as a proxy and a UDP socket posing as a monitoring host: neither
    may ever hear from the client."""
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind(("127.0.0.1", 0))
    proxy.listen(8)
    proxy.settimeout(0.5)
    monitor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    monitor.bind(("127.0.0.1", 0))
    monitor.settimeout(0.5)
    yield proxy, monitor
    proxy.close()
    monitor.close()


def heard_from(listener: socket.socket) -> bool:
    try:
        if listener.type == socket.SOCK_STREAM:
            connection, _ = listener.accept()
            connection.close()
        else:
            listener.recv(4096)
    except TimeoutError:
        return False
    return True


def test_the_client_talks_only_to_its_endpoint_whatever_the_environment(
    fake_s3: str,
    listeners: tuple[socket.socket, socket.socket],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    proxy, monitor = listeners
    junk = f"http://127.0.0.1:{proxy.getsockname()[1]}"
    config = tmp_path / "config"
    config.write_text(
        f"[default]\nendpoint_url = {junk}\nca_bundle = {tmp_path / 'none.pem'}\n"
        f"s3 =\n  addressing_style = virtual\n[profile other]\nendpoint_url = {junk}\n",
        encoding="utf-8",
    )
    # botocore's default loader reads ~/.aws/models before its own data: a rule set there
    # would send every request to the proxy.
    rules = tmp_path / "models" / "s3" / "2006-03-01"
    rules.mkdir(parents=True)
    rule: dict[str, object] = {"conditions": [], "endpoint": {"url": junk}, "type": "endpoint"}
    (rules / "endpoint-rule-set-1.json").write_text(
        json.dumps({"version": "1.0", "parameters": {}, "rules": [rule]}), encoding="utf-8"
    )
    monkeypatch.setattr(Loader, "CUSTOMER_DATA_PATH", str(tmp_path / "models"))
    plugins: list[object] = []

    def load_plugins(client: object, named: object) -> None:
        plugins.append(named)

    monkeypatch.setattr("botocore.session.load_client_plugins", load_plugins)
    for name, value in {
        "HTTP_PROXY": junk,
        "HTTPS_PROXY": junk,
        "ALL_PROXY": junk,
        "http_proxy": junk,
        "https_proxy": junk,
        "AWS_ENDPOINT_URL": junk,
        "AWS_ENDPOINT_URL_S3": junk,
        "AWS_CA_BUNDLE": str(tmp_path / "none.pem"),
        "REQUESTS_CA_BUNDLE": str(tmp_path / "none.pem"),
        "AWS_CONFIG_FILE": str(config),
        "AWS_SHARED_CREDENTIALS_FILE": str(config),
        "AWS_PROFILE": "no-such-profile",
        "AWS_DEFAULT_PROFILE": "no-such-profile",
        "AWS_ACCESS_KEY_ID": "OTHER-KEY",
        "AWS_SECRET_ACCESS_KEY": "other-secret",
        "AWS_SESSION_TOKEN": "other-token",
        "AWS_CSM_ENABLED": "true",
        "AWS_CSM_HOST": "127.0.0.1",
        "AWS_CSM_PORT": str(monitor.getsockname()[1]),
        "AWS_DEFAULTS_MODE": "auto",
        "AWS_DATA_PATH": str(tmp_path / "models"),
        "AWS_REQUEST_CHECKSUM_CALCULATION": "when_supported",
        "AWS_USE_FIPS_ENDPOINT": "true",
        "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "false",
        "BOTOCORE_EXPERIMENTAL__PLUGINS": "fource=fource_test_plugin",
    }.items():
        monkeypatch.setenv(name, value)

    client = make_s3_client(
        fake_s3, access_key="test-key", secret_key="test-secret", region="us-east-1"
    )
    client.head_bucket(Bucket="fource")
    client.put_object(Bucket="fource", Key=KEY, Body=BODY)
    got = client.get_object(Bucket="fource", Key=KEY)["Body"].read()

    assert got == BODY
    host = fake_s3.removeprefix("http://")
    assert [(method, path) for method, path, _ in _FakeS3.seen] == [
        ("HEAD", "/fource"),
        ("PUT", f"/fource/{KEY}"),
        ("GET", f"/fource/{KEY}"),
        ("GET", f"/fource/{KEY}"),  # the region redirect: same host, new signing region
    ]
    for _, _, headers in _FakeS3.seen:
        assert headers["host"] == host
        assert headers["authorization"].startswith("AWS4-HMAC-SHA256 Credential=test-key/")
        assert "x-amz-security-token" not in headers
        assert not [name for name in headers if "checksum" in name]
    put = _FakeS3.seen[1][2]
    assert put["x-amz-content-sha256"] == hashlib.sha256(BODY).hexdigest()  # signed payload
    assert "/eu-west-1/s3/" in _FakeS3.seen[3][2]["authorization"]
    assert not heard_from(proxy)
    assert not heard_from(monitor)
    assert plugins == []


def test_a_busy_server_is_asked_three_times_then_given_up(fake_s3: str) -> None:
    client = make_s3_client(
        fake_s3, access_key="test-key", secret_key="test-secret", region="garage"
    )
    assert (client.meta.endpoint_url, client.meta.region_name) == (fake_s3, "garage")
    with pytest.raises(ClientError):
        client.head_object(Bucket="fource", Key="busy")
    assert [path for _, path, _ in _FakeS3.seen] == ["/fource/busy"] * 3


def test_the_s3_stack_never_logs_at_debug() -> None:
    # botocore logs request headers, Authorization included, at DEBUG; urllib3's warnings name
    # the host (a full connection pool, a header it can't parse).
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        client = make_s3_client(
            "http://127.0.0.1:9", access_key="k", secret_key="s", region="us-east-1"
        )
        for name in ("botocore", "boto3", "s3transfer", "urllib3"):
            assert not logging.getLogger(name).isEnabledFor(logging.DEBUG), name
        assert not logging.getLogger("urllib3").isEnabledFor(logging.WARNING)
        assert vars(client.meta.config)["max_pool_connections"] == 40  # one per worker thread
    finally:
        logging.getLogger().setLevel(logging.WARNING)


def test_boto3_is_imported_only_when_an_s3_name_is_used() -> None:
    script = (
        "import sys, fource.storage\n"
        "assert 'boto3' not in sys.modules and 'botocore' not in sys.modules, 'loaded early'\n"
        "fource.storage.make_s3_client\n"
        "assert 'boto3' in sys.modules, 'not loaded'\n"
    )
    subprocess.run([sys.executable, "-c", script], check=True)
