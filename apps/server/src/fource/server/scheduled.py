"""The scheduled ledger checkpoint (ADR-0014 point 8, ADR-0040): the job a worker runs in every
organisation when FOURCE_LEDGER_CHECKPOINT_MINUTES is set. That setting is the operator's
decision to sign with the installation key; tests sign only with throwaway keys."""

import json
from datetime import timedelta
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import FourceError, Settings
from fource.db import Org
from fource.jobs import Handler, HeldJob, Recurring
from fource.ledger import Checkpoint, EmptyLedger, checkpoint
from fource.server.ledger_commands import checkpoint_file, checkpoint_folder, save_checkpoint

CHECKPOINT = "ledger.checkpoint"


class CheckpointClash(FourceError):
    code = "checkpoint_clash"
    status = 409


def _signs_the_same_entry(file: Path, signed: Checkpoint) -> bool:
    try:
        kept = Checkpoint.from_dict(json.loads(file.read_text(encoding="utf-8")))
    except (OSError, ValueError, RecursionError):
        return False
    return (kept.org, kept.seq, kept.hash) == (signed.org, signed.seq, signed.hash)


def checkpoint_job(
    settings: Settings, private_key: Ed25519PrivateKey, every: timedelta
) -> tuple[Handler, Recurring]:
    """The handler of `ledger.checkpoint` jobs and their schedule."""

    async def sign(session: AsyncSession, job: HeldJob) -> None:
        try:
            signed = await checkpoint(session, private_key)
        except EmptyLedger:
            return  # nothing to vouch for yet
        slug = await session.scalar(select(Org.slug).where(Org.id == job.org_id))
        file = checkpoint_file(checkpoint_folder(settings), slug or str(job.org_id), signed.seq)
        # Written before the commit, so every file signs an entry that exists even if the commit
        # fails. A retry finds its own earlier file for the same entry and keeps it; a file for
        # this seq that signs another hash means the chain was cut and grew again.
        try:
            save_checkpoint(signed, file)
        except FileExistsError:
            if not _signs_the_same_entry(file, signed):
                raise CheckpointClash(
                    f"{file.name} already exists and signs a different entry {signed.seq}: "
                    "the chain may have been cut. Run `just ledger verify`."
                ) from None

    return Handler(sign, lease=timedelta(minutes=2)), Recurring(CHECKPOINT, every=every)
