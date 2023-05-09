import attrs


# Can't use BaseModel due to conflicting inheritances
@attrs.define
class AbstractException(Exception):
    type: str
    title: str | None = None
    status: int | None = None
    detail: str | None = None
    instance: str | None = None


@attrs.define
class BadRequest(AbstractException):
    type: str = "bad request"
    status: int = 400


@attrs.define
class DownloadError(AbstractException):
    type: str = "raster download error"
    status: int = 500


@attrs.define
class MosaickingError(AbstractException):
    type: str = "raster mosaicking error"
    status: int = 500


@attrs.define
class UploadError(AbstractException):
    type: str = "upload error"
    status: int = 500
