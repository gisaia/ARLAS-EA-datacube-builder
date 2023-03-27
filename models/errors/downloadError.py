from fastapi import HTTPException


class DownloadError(HTTPException):

    def __init__(self, msg: str):
        self.status_code = 500
        self.detail = msg
        self.description = "Error while downloading the requested rasters"
