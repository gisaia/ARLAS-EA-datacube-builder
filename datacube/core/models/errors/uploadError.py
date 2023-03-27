from fastapi import HTTPException


class UploadError(HTTPException):

    def __init__(self, msg: str):
        self.status_code = 500
        self.detail = msg
        self.description = "Error while uploading file"
