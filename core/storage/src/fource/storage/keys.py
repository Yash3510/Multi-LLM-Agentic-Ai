"""Where a stored file's bytes live: a key built from ids only (ADR-0044)."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class BlobKey:
    """The bytes of one file, `<organisation uuid hex>/<file uuid hex>`. Made of two UUIDs and
    nothing else, so a key can never point outside its organisation's folder or prefix."""

    org: uuid.UUID
    file: uuid.UUID

    @property
    def path(self) -> str:
        return f"{self.org.hex}/{self.file.hex}"
