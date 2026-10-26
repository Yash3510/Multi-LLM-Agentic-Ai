import uuid

from fource.common import FourceError


class LeaseLost(RuntimeError):
    """Another worker took the job after this one's lease ran out. The attempt's writes must
    roll back: only the current holder may finish a job."""

    def __init__(self, job_id: uuid.UUID) -> None:
        super().__init__(f"job {job_id} was taken by another worker")
        self.job_id = job_id


class Unfinished(FourceError):
    """What a job records when its last attempt never finished (its worker stopped, or the
    attempt outlived its lease)."""

    code = "job_unfinished"
    status = 500
