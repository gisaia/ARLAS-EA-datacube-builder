from typing import Annotated
from fastapi import Query
from pydantic import BaseModel

from .rasterProductType import RasterProductType

TYPE_DESCRIPTION = "The type of the raster file."
PATH_DESCRIPTION = "The path to the raster file."
ID_DESCRIPTION = "Identifier for the raster file, " + \
    "used for the traceability of the datacube."


class RasterFile(BaseModel):
    type: Annotated[RasterProductType, Query(description=TYPE_DESCRIPTION)]
    path: Annotated[str, Query(description=PATH_DESCRIPTION)]
    id: Annotated[str, Query(description=ID_DESCRIPTION)]
