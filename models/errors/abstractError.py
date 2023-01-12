import abc
from dataclasses import dataclass


@dataclass
class AbstractError(Exception, abc.ABC):
    code: int
    description: str

    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return {
            "code": self.code,
            "description": self.description,
            "message": self.message
        }
