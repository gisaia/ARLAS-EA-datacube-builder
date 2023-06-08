from fastapi import APIRouter
import fastapi

from datacube.core.build_cube import build_datacube
from datacube.core.models.cubeBuildResult import CubeBuildResult
from datacube.core.models.request.cubeBuild import (CubeBuildRequest,
                                                    ExtendedCubeBuildRequest)
from datacube.rest.models.restException import RESTException
from datacube.rest.server.server_configuration import ServerConfiguration

ROUTER = APIRouter()


def build_datacube_wrapper(request: CubeBuildRequest) -> CubeBuildResult:
    return build_datacube(ExtendedCubeBuildRequest(
        request, ServerConfiguration.is_pivot_format()))


@ROUTER.post("/cube/build",
             response_model_exclude_none=True,
             responses={
                fastapi.status.HTTP_200_OK: {
                    'model': CubeBuildResult
                },
                fastapi.status.HTTP_400_BAD_REQUEST: {
                    'model': RESTException
                },
                fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    'model': RESTException
                },
                fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    'model': RESTException
                }
             })
async def cube_build(request: CubeBuildRequest):
    return build_datacube_wrapper(request)
