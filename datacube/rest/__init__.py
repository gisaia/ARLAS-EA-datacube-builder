from .cube_build import ROUTER as cube_build_router
from .ogc.conformance import ROUTER as conformance_router
from .ogc.job import ROUTER as job_router
from .ogc.landing_page import ROUTER as landing_page_router
from .ogc.process import ROUTER as process_router

ROUTERS = [
    cube_build_router,
    landing_page_router,
    conformance_router,
    process_router,
    job_router
]
