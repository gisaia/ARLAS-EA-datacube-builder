from fastapi import HTTPException


class MosaickingError(HTTPException):

    def __init__(self, msg: str):
        self.status_code = 500
        self.detail = msg
        self.description = "Error when mosaicking the rasters"
