from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest

from fource.ledger import GENESIS, Entry, EntryType, canonical, format_time, make_entry, sha256_hex

ORG = "0192f5a0-0000-7000-8000-000000000001"
USER = "0192f5a0-0000-7000-8000-0000000000aa"
BASE: dict[str, Any] = {
    "seq": 1,
    "at": "2026-11-14T10:22:31.512Z",
    "org": ORG,
    "type": "checkpoint",
    "actor": "system",
    "prev": GENESIS,
}

# A fixed vector: a verifier written in any language must reproduce these bytes and hash.
FIRST_CANONICAL = (
    '{"actor":"system","at":"2026-11-14T10:22:31.512Z","case":null,"inputs_sha256":null,'
    '"org":"0192f5a0-0000-7000-8000-000000000001","outputs_sha256":null,'
    '"prev":"0000000000000000000000000000000000000000000000000000000000000000",'
    '"refs":{"roles":"Admin","user":"0192f5a0-0000-7000-8000-0000000000aa"},'
    '"run":null,"seq":1,"type":"identity.user.create"}'
)
FIRST_HASH = "29c04f35f9fa3620715310e44047300b908992276697f036c12778ffae208585"


def entry(**change: Any) -> Entry:
    return make_entry(**{**BASE, **change})


def test_the_fixed_vector() -> None:
    first = entry(type=EntryType.USER_CREATE, refs={"user": USER, "roles": "Admin"})
    assert canonical(first.fields()).decode() == FIRST_CANONICAL
    assert first.hash == FIRST_HASH == sha256_hex(FIRST_CANONICAL.encode())
    assert first.to_dict() == {**first.fields(), "hash": FIRST_HASH}


def test_every_field_is_covered_by_the_hash() -> None:
    changes: list[dict[str, Any]] = [
        {"seq": 2},
        {"at": "2026-11-14T10:22:31.513Z"},
        {"org": USER},
        {"type": "identity.signout"},
        {"actor": "anonymous"},
        {"prev": "1" * 64},
        {"run": USER},
        {"case": USER},
        {"inputs_sha256": "a" * 64},
        {"outputs_sha256": "b" * 64},
        {"refs": {"user": USER}},
    ]
    hashes = {entry().hash} | {entry(**change).hash for change in changes}
    assert len(hashes) == len(changes) + 1


def test_the_canonical_form_sorts_keys_and_keeps_text_as_utf8() -> None:
    assert canonical({"b": 1, "a": "é\n"}) == b'{"a":"\xc3\xa9\\n","b":1}'


def test_times_are_utc_with_milliseconds() -> None:
    india = timezone(timedelta(hours=5, minutes=30))
    moment = datetime(2026, 11, 14, 15, 52, 31, 512999, tzinfo=india)
    assert format_time(moment) == "2026-11-14T10:22:31.512Z"
    assert format_time(datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)) == "2026-01-02T03:04:05.000Z"


@pytest.mark.parametrize(
    "change",
    [
        {"seq": 0},
        {"seq": True},
        {"at": "2026-11-14 10:22:31"},
        {"org": ""},
        {"type": "Not.A.Type"},
        {"actor": "someone else"},
        {"prev": "short"},
        {"inputs_sha256": "A" * 64},
        {"refs": {"Bad-Key": "x"}},
        {"refs": {"user": "a\x00b"}},
        {"refs": {"user": "x" * 1001}},
    ],
)
def test_malformed_entries_are_refused(change: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        entry(**change)
