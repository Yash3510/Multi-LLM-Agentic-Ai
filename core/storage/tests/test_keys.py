import re
import types
import uuid
from typing import cast

import pytest

from fource.storage import BlobKey

ORG = uuid.UUID("0190a0b1-0000-7000-8000-000000000001")
FILE = uuid.UUID("0190a0b1-0000-7000-8000-0000000000ff")


class OddUuid(uuid.UUID):
    @property
    def hex(self) -> str:
        return "/etc"


def make(org: object, file: object) -> BlobKey:
    return BlobKey(cast(uuid.UUID, org), cast(uuid.UUID, file))


def test_two_plain_uuids_make_a_key_of_two_hex_names() -> None:
    assert re.fullmatch(r"[0-9a-f]{32}/[0-9a-f]{32}", BlobKey(ORG, FILE).path)


@pytest.mark.parametrize(
    "part",
    [
        OddUuid(int=ORG.int),
        str(ORG),
        types.SimpleNamespace(hex="../../etc"),
        None,
    ],
    ids=["subclass", "string", "namespace", "none"],
)
def test_anything_but_a_plain_uuid_is_refused(part: object) -> None:
    with pytest.raises(TypeError, match="two UUIDs"):
        make(part, FILE)
    with pytest.raises(TypeError, match="two UUIDs"):
        make(ORG, part)
