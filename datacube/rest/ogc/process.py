from fastapi import APIRouter, status

from datacube.core.build_cube import build_datacube
from datacube.core.models.cubeBuildResult import CubeBuildResult
from datacube.core.models.request.cubeBuild import CubeBuildRequest
from datacube.rest.ogc.models import (ExceptionType, JobControlOptions, Link,
                                      OGCException, ProcessDescription,
                                      ProcessList, ProcessListItem,
                                      ProcessSummary, TransmissionMode)
from datacube.rest.ogc.utils import base_model2description, json_http_error
from datacube.rest.serverConfiguration import ServerConfiguration

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
        process=DC3_BUILDER_PROCESS, method=build_datacube)
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
            response_model_exclude_none=True,
            responses={
                status.HTTP_200_OK: {
                    'model': ProcessDescription
                    },
                status.HTTP_404_NOT_FOUND: {
                    'model': OGCException
                }
            })
def get_process_summary(process_id: str):
    if process_id not in PROCESSES.keys():
        return json_http_error(status.HTTP_404_NOT_FOUND,
                               ExceptionType.URI_NOT_FOUND.value,
                               detail=f"'{process_id}' is not a valid id.")
    return PROCESSES[process_id].process
