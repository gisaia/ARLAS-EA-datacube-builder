from .abstractError import AbstractError


class BadRequest(AbstractError):
    code = 400
    description = "Bad request"
