from fastapi import APIRouter

from datacube.core.build_cube import build_datacube
from datacube.core.models.cubeBuildResult import CubeBuildResult
from datacube.core.models.request.cubeBuild import (CubeBuildRequest,
                                                    ExtendedCubeBuildRequest)
from datacube.rest.server.server_configuration import ServerConfiguration

ROUTER = APIRouter()


def build_datacube_wrapper(request: CubeBuildRequest) -> CubeBuildResult:
    return build_datacube(ExtendedCubeBuildRequest(
        request, ServerConfiguration.is_pivot_format()))


@ROUTER.post("/cube/build",
             response_model=CubeBuildResult,
             response_model_exclude_none=True)
async def cube_build(request: CubeBuildRequest):
    return build_datacube_wrapper(request)
