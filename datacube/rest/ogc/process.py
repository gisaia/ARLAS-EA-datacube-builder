from fastapi import APIRouter, status
from pydantic import BaseModel

from datacube.core.models.cubeBuildResult import CubeBuildResult
from datacube.core.models.exception import AbstractException as OGCException
from datacube.core.models.request.cubeBuild import CubeBuildRequest
from datacube.rest.cube_build import build_datacube_wrapper
from datacube.rest.models.restException import RESTException
from datacube.rest.ogc.models import (ExceptionType, Execute,
                                      JobControlOptions, Link,
                                      ProcessDescription, ProcessList,
                                      ProcessListItem, ProcessSummary,
                                      TransmissionMode)
from datacube.rest.ogc.utils import base_model2description, execute2inputs
from datacube.rest.server.server_configuration import ServerConfiguration

ROUTER = APIRouter()
DC3_BUILDER_PROCESS = ProcessDescription(
    title="Datacube Builder",
    description="OGC description of a 'Datacube Builder' process",
    id="dc3-builder",
    version="1.0.0",
    jobControlOptions=[JobControlOptions.sync_execute],
    outputTransmission=[TransmissionMode.reference],
    inputs=base_model2description(CubeBuildRequest),
    outputs=base_model2description(CubeBuildResult)
)


PROCESSES: dict[str, ProcessListItem] = {
    DC3_BUILDER_PROCESS.id: ProcessListItem(
        process=DC3_BUILDER_PROCESS,
        method=build_datacube_wrapper,
        input_model=CubeBuildRequest)
}


def __create_process_link(process: ProcessDescription) -> Link:
    return Link(
        href=f"{ServerConfiguration.get_server_root()}/processes/{process.id}",
        title=f"Link for the {process.description}")


@ROUTER.get("/processes",
            response_model=ProcessList,
            response_model_exclude_none=True)
def get_processes_list() -> ProcessList:
    processes: list[ProcessSummary] = []
    links: list[Link] = []

    for process in PROCESSES.values():
        processes.append(ProcessSummary(**process.process.dict()))
        links.append(__create_process_link(process.process))

    return ProcessList(
        processes=processes,
        links=links
    )


@ROUTER.get("/processes/{process_id}",
            response_model=ProcessDescription,
            response_model_exclude_unset=True,
            responses={
                status.HTTP_200_OK: {
                    'model': ProcessDescription
                    },
                status.HTTP_404_NOT_FOUND: {
                    'model': RESTException
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    'model': RESTException
                }
            })
def get_process_summary(process_id: str):
    if process_id not in PROCESSES.keys():
        raise OGCException(type=ExceptionType.URI_NOT_FOUND.value,
                           status=status.HTTP_404_NOT_FOUND,
                           detail=f"'{process_id}' is not a valid id.")
    return PROCESSES[process_id].process


@ROUTER.post("/processes/{process_id}/execution",
             response_model_exclude_none=True,
             responses={
                status.HTTP_200_OK: {
                    'model': BaseModel
                    },
                status.HTTP_404_NOT_FOUND: {
                    'model': RESTException
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    'model': RESTException
                }
             })
def post_process_execute(process_id: str, execute: Execute):
    if process_id not in PROCESSES.keys():
        raise OGCException(type=ExceptionType.URI_NOT_FOUND.value,
                           status=status.HTTP_404_NOT_FOUND,
                           detail=f"'{process_id}' is not a valid id.")
    process = PROCESSES[process_id]

    return process.method(process.input_model(**execute2inputs(execute)))
