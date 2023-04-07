from fastapi import APIRouter

from datacube.core.build_cube import build_datacube
from datacube.core.models.cubeBuildResult import CubeBuildResult
from datacube.core.models.request.cubeBuild import (CubeBuildRequest,
                                                    ExtendedCubeBuildRequest)

ROUTER = APIRouter()


@ROUTER.post("/cube/build",
             response_model=CubeBuildResult,
             response_model_exclude_none=True)
async def cube_build(request: CubeBuildRequest):
    return build_datacube(ExtendedCubeBuildRequest(request))
