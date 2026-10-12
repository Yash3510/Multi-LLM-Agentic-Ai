import os
import time
import uuid


def new_id() -> uuid.UUID:
    """A UUIDv7: 48 bits of Unix milliseconds then random bits, so ids sort by creation time.

    Python 3.12 has no uuid.uuid7, so the layout from RFC 9562 is built here.
    """
    millis = time.time_ns() // 1_000_000
    value = (millis & 0xFFFF_FFFF_FFFF) << 80 | int.from_bytes(os.urandom(10), "big")
    value = (value & ~(0xF << 76)) | (0x7 << 76)  # version 7
    value = (value & ~(0x3 << 62)) | (0x2 << 62)  # the RFC 9562 variant
    return uuid.UUID(int=value)
