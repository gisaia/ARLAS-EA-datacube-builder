import enum


class JobType(enum.Enum):
    process = "process"


class StatusCode(enum.Enum):
    accepted: str = "accepted"
    running: str = "running"
    successful: str = "successful"
    failed: str = "failed"
    dismissed: str = "dismissed"

