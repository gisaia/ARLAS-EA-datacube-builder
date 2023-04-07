from fastapi import APIRouter, status

from datacube.rest.ogc.models import StatusInfo, ExceptionType
from datacube.rest.ogc.models.execute import InlineOrRefData
from datacube.rest.ogc.utils import json_http_error


ROUTER = APIRouter()


@ROUTER.get("/jobs",
            response_model_exclude_none=True)
def get_jobs():
    return json_http_error(status.HTTP_501_NOT_IMPLEMENTED,
                           ExceptionType.NOT_IMPLEMENTED.value)


@ROUTER.get("/jobs/{jobId}",
            response_model=StatusInfo,
            response_model_exclude_none=True)
def get_job(jobId: str):
    return json_http_error(status.HTTP_501_NOT_IMPLEMENTED,
                           ExceptionType.NOT_IMPLEMENTED.value)


@ROUTER.delete("/jobs/{jobId}",
               response_model=StatusInfo,
               response_model_exclude_none=True)
def delete_job(jobId: str):
    return json_http_error(status.HTTP_501_NOT_IMPLEMENTED,
                           ExceptionType.NOT_IMPLEMENTED.value)


@ROUTER.get("/jobs/{jobId}/results",
            response_model=dict[str, InlineOrRefData],
            response_model_exclude_none=True)
def get_job_result(jobId: str):
    return json_http_error(status.HTTP_501_NOT_IMPLEMENTED,
                           ExceptionType.NOT_IMPLEMENTED.value)
