from fastapi import HTTPException


class BadRequest(HTTPException):
    def __init__(self, msg: str):
        self.status_code = 400
        self.detail = msg
