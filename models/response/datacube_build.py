from typing import Annotated
from fastapi import Query
from pydantic import BaseModel

DC_URL_DESCRIPTION = "URL at which the datacube is created"
PREVIEW_URL_DESCRIPTION = "URL at which the datacube's preview is created"
PREVIEW_DESCRIPTION = "The preview of the datacube encoded in base64"


class DatacubeBuildResponse(BaseModel):
    datacubeURL: Annotated[str, Query(description=DC_URL_DESCRIPTION)]
    previewURL: Annotated[str, Query(description=PREVIEW_URL_DESCRIPTION)]
    preview: Annotated[str, Query(description=PREVIEW_DESCRIPTION)]
