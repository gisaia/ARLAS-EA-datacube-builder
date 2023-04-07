from fastapi import APIRouter

from datacube.rest.ogc.models import LandingPage, Link
from datacube.rest.serverConfiguration import ServerConfiguration

ROUTER = APIRouter()


@ROUTER.get("/",
            response_model=LandingPage,
            response_model_exclude_none=True)
def get_landing_page() -> LandingPage:
    server_root = ServerConfiguration.get_server_root()

    api_definition = Link(
        href=server_root + "/openapi.json",
        rel="service-desc",
        type="application/vnd.oai.openapi+json;version=3.0",
        title="OpenAPI service description",
    )
    conformance = Link(
        href=server_root + "/conformace",
        rel="http://www.opengis.net/def/rel/ogc/1.0/conformance",
        type="application/json",
        title="OGC API - Processes conformance classes " +
              "implemented by this server"
    )
    processes = Link(
        href=server_root + "/processes",
        rel="http://www.opengis.net/def/rel/ogc/1.0/processes",
        type="application/json",
        title="Metadata about the processes"
    )
    jobs = Link(
        href=server_root + "/jobs",
        rel="http://www.opengis.net/def/rel/ogc/1.0/job-list",
        title="The endpoint for job monitoring"
    )

    return LandingPage(
        title="Datacube Builder API",
        description="OGC processes complaint API",
        links=[
            api_definition, conformance, processes, jobs
        ]
    )
