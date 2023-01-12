from .abstractError import AbstractError


class DownloadError(AbstractError):
    code = 500
    description = "Error while downloading the requested rasters"
