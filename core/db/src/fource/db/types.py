from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UtcDateTime(TypeDecorator[datetime]):
    """A timestamp stored in UTC and always read back aware, on SQLite and PostgreSQL alike.

    SQLite has no time zones, so values are stored as naive UTC and labelled UTC on the way out.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect | None
    ) -> datetime | None:
        return None if value is None else value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(
        self, value: datetime | None, dialect: Dialect | None
    ) -> datetime | None:
        return None if value is None else value.replace(tzinfo=UTC)
