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
    NOT_IMPLEMENTED = "The endpoint is not implemented."


class JobType(enum.Enum):
    process = "process"


class StatusCode(enum.Enum):
    accepted: str = "accepted"
    running: str = "running"
    successful: str = "successful"
    failed: str = "failed"
    dismissed: str = "dismissed"


class Response(enum.Enum):
    raw = "raw"
    document = "document"


class Crs(enum.Enum):
    http___www_opengis_net_def_crs_OGC_1_3_CRS84 = (
        "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
    )
    http___www_opengis_net_def_crs_OGC_0_CRS84h = (
        "http://www.opengis.net/def/crs/OGC/0/CRS84h"
    )
