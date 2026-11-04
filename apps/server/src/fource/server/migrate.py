from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from fource.common import Settings


def alembic_config(url: str) -> Config:
    """Alembic's configuration, built in code; the history lives in this package."""
    config = Config()
    config.set_main_option("script_location", "fource.server:migrations")
    # Config is a ConfigParser, which reads % as interpolation: double it to keep it.
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def migration_url(settings: Settings) -> str:
    """PostgreSQL migrates as the owner role; SQLite uses the one database URL."""
    url = settings.database_admin_url or settings.database_url
    return url.get_secret_value()


def upgrade(url: str, revision: str = "head") -> None:
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite" and parsed.database not in (None, "", ":memory:"):
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)  # as Database does
    command.upgrade(alembic_config(url), revision)


def downgrade(url: str, revision: str) -> None:
    command.downgrade(alembic_config(url), revision)
