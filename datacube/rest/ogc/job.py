from fastapi import APIRouter


ROUTER = APIRouter()


@ROUTER.get("/jobs",
            response_model_exclude_none=True)
def get_jobs():
    return {"jobs": [], "links": []}
