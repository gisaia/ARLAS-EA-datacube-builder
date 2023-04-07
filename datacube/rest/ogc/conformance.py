from fastapi import APIRouter

from datacube.rest.ogc.models import Conforms

ROUTER = APIRouter()
ROOT_CONFORMANCE = "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf"


@ROUTER.get("/conformance", response_model_exclude_none=True)
def get_conformance() -> Conforms:
    return Conforms(
        conformsTo=[
            f"{ROOT_CONFORMANCE}/core",
            f"{ROOT_CONFORMANCE}/ogc-process-description",
            f"{ROOT_CONFORMANCE}/job-list",
            f"{ROOT_CONFORMANCE}/json",
            f"{ROOT_CONFORMANCE}/oas30",
        ]
    )
