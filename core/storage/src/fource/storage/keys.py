"""Where a stored file's bytes live: a key built from ids only (ADR-0044)."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class BlobKey:
    """The bytes of one file, `<organisation uuid hex>/<file uuid hex>`. Made of two UUIDs and
    nothing else, so a key can never point outside its organisation's folder or prefix."""

    org: uuid.UUID
    file: uuid.UUID

    def __post_init__(self) -> None:
        # Exact type, not isinstance: a subclass can override `hex` to return any text.
        if type(self.org) is not uuid.UUID or type(self.file) is not uuid.UUID:
            raise TypeError("A blob key is two UUIDs.")

    @property
    def path(self) -> str:
        return f"{self.org.hex}/{self.file.hex}"
