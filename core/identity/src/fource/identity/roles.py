from enum import StrEnum


class Role(StrEnum):
    """What a person may do (master plan §7.3). Packs map their own role names onto these."""

    ADMIN = "Admin"
    AUTHOR = "Author"
    REVIEWER = "Reviewer"
    VIEWER = "Viewer"
    AUDITOR = "Auditor"
    PACK_AUTHOR = "Pack Author"
    PACK_APPROVER = "Pack Approver"
