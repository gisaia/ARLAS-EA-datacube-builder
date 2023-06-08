from fastapi import APIRouter, status

from datacube.core.models.exception import AbstractException as OGCException
from datacube.rest.models.restException import RESTException
from datacube.rest.ogc.models import ExceptionType, StatusInfo
from datacube.rest.ogc.models.execute import InlineOrRefData

ROUTER = APIRouter()


@ROUTER.get("/jobs",
            response_model_exclude_none=True)
def get_jobs():
    raise OGCException(type=ExceptionType.NOT_IMPLEMENTED.value,
                       status=status.HTTP_501_NOT_IMPLEMENTED)


@ROUTER.get("/jobs/{jobId}",
            response_model_exclude_none=True,
            responses={
                status.HTTP_200_OK: {
                    'model': StatusInfo
                    },
                status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    'model': RESTException
                }
            })
def get_job(jobId: str):
    raise OGCException(type=ExceptionType.NOT_IMPLEMENTED.value,
                       status=status.HTTP_501_NOT_IMPLEMENTED)


@ROUTER.delete("/jobs/{jobId}",
               response_model_exclude_none=True,
               responses={
                status.HTTP_200_OK: {
                    'model': StatusInfo
                    },
                status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    'model': RESTException
                }
               })
def delete_job(jobId: str):
    raise OGCException(type=ExceptionType.NOT_IMPLEMENTED.value,
                       status=status.HTTP_501_NOT_IMPLEMENTED)


@ROUTER.get("/jobs/{jobId}/results",
            response_model_exclude_none=True,
            responses={
                status.HTTP_200_OK: {
                    'model': dict[str, InlineOrRefData]
                    },
                status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    'model': RESTException
                }
            })
def get_job_result(jobId: str):
    raise OGCException(type=ExceptionType.NOT_IMPLEMENTED.value,
                       status=status.HTTP_501_NOT_IMPLEMENTED)
