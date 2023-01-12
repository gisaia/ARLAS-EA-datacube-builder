from .abstractError import AbstractError


class UploadError(AbstractError):
    code = 500
    description = "Error while uploading file"
