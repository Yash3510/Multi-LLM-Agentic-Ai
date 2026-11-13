import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from fource.db import Database
from fource.storage import (
    BlobKey,
    FileDamaged,
    FileNotFound,
    FileTooLarge,
    StorageUnavailable,
    StoredFile,
)

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0190a0b1-0000-7000-8000-000000000001")
FILE = uuid.UUID("0190a0b1-0000-7000-8000-0000000000ff")


def a_file(size: int = 5) -> StoredFile:
    return StoredFile(
        name="notes.txt",
        content_type="text/plain",
        size=size,
        sha256="0" * 64,
        created_by="system",
    )


def test_a_blob_key_is_two_uuids_in_hex() -> None:
    expected = "0190a0b1000070008000000000000001/0190a0b10000700080000000000000ff"
    assert BlobKey(ORG, FILE).path == expected


def test_errors_carry_their_codes_and_statuses() -> None:
    errors = (StorageUnavailable, FileNotFound, FileTooLarge, FileDamaged)
    assert [(error.code, error.status) for error in errors] == [
        ("storage_unavailable", 503),
        ("file_not_found", 404),
        ("file_too_large", 413),
        ("file_damaged", 500),
    ]


async def test_a_record_belongs_to_one_organisation(
    orgs: tuple[Database, uuid.UUID, uuid.UUID],
) -> None:
    database, first, second = orgs
    async with database.org_session(first) as session:
        session.add(a_file())
    async with database.org_session(first) as session:
        mine = (await session.scalars(select(StoredFile))).all()
    async with database.org_session(second) as session:
        theirs = (await session.scalars(select(StoredFile))).all()
    assert [(row.org_id, row.size, row.deleted_at) for row in mine] == [(first, 5, None)]
    assert theirs == []


async def test_a_size_below_zero_is_refused(orgs: tuple[Database, uuid.UUID, uuid.UUID]) -> None:
    database, first, _ = orgs
    with pytest.raises(IntegrityError, match="stored_files_size|CHECK"):
        async with database.org_session(first) as session:
            session.add(a_file(size=-1))
