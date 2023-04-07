import enum


class TransmissionMode(enum.Enum):
    value: str = "value"
    reference: str = "reference"


class JobControlOptions(enum.Enum):
    sync_execute: str = "sync-execute"
    async_execute: str = "async-execute"
    dismiss: str = "dismiss"


class MaxOccur(enum.Enum):
    unbounded = "unbounded"


class ObjectType(enum.Enum):
    array = "array"
    boolean = "boolean"
    integer = "integer"
    number = "number"
    object = "object"
    string = "string"


class ExceptionType(enum.Enum):
    URI_NOT_FOUND = "The requested URI was not found."
    SERVER_ERROR = "A server error occurred."


class JobType(enum.Enum):
    process = "process"


class StatusCode(enum.Enum):
    accepted: str = "accepted"
    running: str = "running"
    successful: str = "successful"
    failed: str = "failed"
    dismissed: str = "dismissed"
