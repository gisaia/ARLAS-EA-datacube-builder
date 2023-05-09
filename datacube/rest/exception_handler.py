import fastapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request
from pydantic import BaseModel

from typing import Callable
from datacube.rest.models.restException import RESTException
from datacube.core.models.exception import AbstractException
from datacube.core.logging.logger import CustomLogger as Logger

LOGGER = Logger.get_logger()


HandledExceptions = RequestValidationError | AbstractException


class ExceptionHandler(BaseModel, arbitrary_types_allowed=True):
    exception: type[HandledExceptions]
    handler: Callable[[Request, HandledExceptions], JSONResponse]


def validation_exception_handler(req: Request, exc: RequestValidationError):
    # Format the detail of the error message
    detail = ""
    for error in exc.errors():
        loc = error["loc"][1]
        for i in range(2, len(error["loc"])):
            if isinstance(error["loc"][i], str):
                loc += f'.{error["loc"][i]}'
            elif isinstance(error["loc"][i], int):
                loc += f'[{str(error["loc"][i])}]'
        detail += f'{loc}: {error["msg"]}\n'
    detail = detail[:-1]

    return JSONResponse(content=RESTException(
            type="bad request",
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="validation error",
            detail=detail,
            instance=str(req.url)).dict(exclude_none=True),
        status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY)


def server_error_handler(req: Request, exc: AbstractException):
    return JSONResponse(content=RESTException(
            type=exc.type,
            status_code=exc.status,
            title=exc.title,
            detail=exc.detail,
            instance=str(req.url)).dict(exclude_none=True),
        status_code=exc.status if exc.status is not None
        else fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR)


EXCEPTION_HANDLERS: list[ExceptionHandler] = [
    ExceptionHandler(exception=RequestValidationError,
                     handler=validation_exception_handler),
    ExceptionHandler(exception=AbstractException,
                     handler=server_error_handler)
]
