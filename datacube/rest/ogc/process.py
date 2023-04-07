from fastapi import APIRouter

from datacube.core.build_cube import build_datacube
from datacube.core.models.cubeBuildResult import CubeBuildResult
from datacube.core.models.request.cubeBuild import CubeBuildRequest
from datacube.rest.ogc.models import (JobControlOptions, Link,
                                      ProcessDescription, ProcessList,
                                      ProcessListItem, ProcessSummary,
                                      TransmissionMode)
from datacube.rest.ogc.utils import base_model2description
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


@ROUTER.get("/processes", response_model_exclude_none=True)
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
