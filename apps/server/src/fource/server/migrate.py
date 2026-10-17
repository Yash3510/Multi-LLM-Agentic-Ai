from alembic import command
from alembic.config import Config

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
    command.upgrade(alembic_config(url), revision)


def downgrade(url: str, revision: str) -> None:
    command.downgrade(alembic_config(url), revision)
