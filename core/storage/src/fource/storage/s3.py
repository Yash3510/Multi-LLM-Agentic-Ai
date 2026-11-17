"""Bytes in an S3 bucket (MinIO), through boto3 (ADR-0044).

Only this module imports boto3, and only `open_storage` with FOURCE_STORAGE=s3 (or the
package's lazy exports) imports this module. botocore facts relied on here, as of 1.43.123,
are listed in docs/architecture/storage.md.
"""

import logging
import os
from typing import TYPE_CHECKING

import boto3.session
import botocore.session
from botocore.config import Config
from botocore.configprovider import (
    BOTOCORE_DEFAUT_SESSION_VARIABLES,
    ConfigChainFactory,
    ConstantProvider,
)
from botocore.loaders import Loader
from botocore.plugin import PluginContext, reset_plugin_context, set_plugin_context

if TYPE_CHECKING:
    from types_boto3_s3.client import S3Client

# botocore logs every request's headers, Authorization included, at DEBUG: keep the whole S3
# stack above that, whatever level the root logger is given. urllib3's warnings name the host
# (a full connection pool, a header it can't parse), so it stays above those too.
for _name in ("botocore", "boto3", "s3transfer"):
    logging.getLogger(_name).setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.ERROR)

CONNECT_SECONDS = 5
READ_SECONDS = 60
ATTEMPTS = 3
POOL_CONNECTIONS = 40  # anyio's default thread limit: a connection for each worker thread


def _isolated_session() -> botocore.session.Session:
    """A botocore session that takes nothing from the environment or from files: no profile,
    no ~/.aws config or credentials file, no data path, no service data from ~/.aws/models,
    no client-side monitoring, no CA bundle, region, retry or endpoint setting. Uses
    botocore's config_store component, the way botocore's own session code recommends for
    changing lookups."""
    session = botocore.session.Session()
    store = session.get_component("config_store")
    chains = ConfigChainFactory(session=session, environ={})
    for name, (_, _, default, convert) in BOTOCORE_DEFAUT_SESSION_VARIABLES.items():
        chain = chains.create_config_chain(
            instance_name=name, default=default, conversion_func=convert
        )
        store.set_config_provider(name, chain)
    for name in ("config_file", "credentials_file"):
        store.set_config_provider(name, ConstantProvider(os.devnull))
    for name in ("s3", "proxies_config"):
        store.set_config_provider(name, ConstantProvider(None))
    # Set here, not in Config: botocore takes both, but its type stubs don't know the first and
    # mistype the second. "legacy" never asks the instance for its region; configured
    # endpoint URLs could only come from the environment or files, which this session ignores.
    store.set_config_provider("ignore_configured_endpoint_urls", ConstantProvider(True))
    store.set_config_provider("defaults_mode", ConstantProvider("legacy"))
    # The default loader reads ~/.aws/models before botocore's own data, so a file there could
    # replace S3's endpoint rules: read botocore's own data only.
    session.register_component(
        "data_loader",
        Loader(extra_search_paths=[Loader.BUILTIN_DATA_PATH], include_default_search_paths=False),
    )
    return session


def make_s3_client(
    endpoint: str,
    *,
    access_key: str,
    secret_key: str,
    region: str,
    connect_timeout: float = CONNECT_SECONDS,
    read_timeout: float = READ_SECONDS,
    attempts: int = ATTEMPTS,
) -> "S3Client":
    """One S3 client that talks to `endpoint` and nowhere else: explicit credentials (no
    provider chain, no instance metadata), TLS checked against the default trust store, no
    proxy, no plugin, path-style addressing, bounded time and attempts, and every PUT's body
    signed by its SHA-256 (request checksums only where an operation requires one)."""
    config = Config(
        signature_version="s3v4",
        s3={"addressing_style": "path", "payload_signing_enabled": True},
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        retries={"mode": "standard", "total_max_attempts": attempts},
        proxies={},
        use_fips_endpoint=False,
        use_dualstack_endpoint=False,
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
        max_pool_connections=POOL_CONNECTIONS,
    )
    session = boto3.session.Session(botocore_session=_isolated_session())
    # Every new client imports the modules BOTOCORE_EXPERIMENTAL__PLUGINS names and hands itself
    # to them; botocore turns that off this way for the clients it creates itself.
    token = set_plugin_context(PluginContext(plugins="DISABLED"))
    try:
        client: S3Client = session.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            verify=True,
            config=config,
        )
    finally:
        reset_plugin_context(token)
    return client
