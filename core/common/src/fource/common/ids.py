import os
import threading
import time
import uuid

_lock = threading.Lock()
_last_millis = 0
_last_counter = 0


def new_id() -> uuid.UUID:
    """A UUIDv7: 48 bits of Unix milliseconds, then 74 counter bits, version and variant set.

    Ids made in one process sort in creation order (RFC 9562, section 6.2): ids in the same
    millisecond count up from the last one. Ids from different processes only sort by
    millisecond.

    Python 3.12 has no uuid.uuid7, so the layout from RFC 9562 is built here.
    """
    global _last_millis, _last_counter
    with _lock:
        millis = time.time_ns() // 1_000_000
        if millis > _last_millis:
            _last_millis = millis
            # 73 random bits, not 74, so the counter can count up without overflowing 74 bits.
            _last_counter = int.from_bytes(os.urandom(10), "big") >> 7
        else:
            # Same millisecond, or the clock stepped back: stay on the last millisecond and
            # count up, so ids never sort backwards because the clock did.
            _last_counter += 1
        millis, counter = _last_millis, _last_counter
    rand_a = counter >> 62
    rand_b = counter & ((1 << 62) - 1)
    value = (millis & 0xFFFF_FFFF_FFFF) << 80 | 0x7 << 76 | rand_a << 64 | 0x2 << 62 | rand_b
    return uuid.UUID(int=value)
