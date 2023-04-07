from fastapi import APIRouter

from datacube.core.models.request.cubeBuild import CubeBuildRequest, \
                                                   ExtendedCubeBuildRequest
from datacube.core.build_cube import build_datacube

ROUTER = APIRouter()


@ROUTER.post("/cube/build")
async def cube_build(request: CubeBuildRequest):
    return build_datacube(ExtendedCubeBuildRequest(request))
