from .abstractError import AbstractError


class MosaickingError(AbstractError):
    code = 500
    description = "Error when mosaicking the rasters"
