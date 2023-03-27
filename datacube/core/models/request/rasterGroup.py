from typing import Annotated, List, Dict
from fastapi import Query
from pydantic import BaseModel

from datacube.core.models.request.rasterFile import RasterFile

RASTERS_DESCRIPTION = "The list of raster files in this group."
TIMESTAMP_DESCRIPTION = "The timestamp of this group."
METADATA_DESCRIPTION = "Optional metadata for this group."


class RasterGroup(BaseModel):
    rasters: Annotated[List[RasterFile],
                       Query(description=RASTERS_DESCRIPTION)]
    timestamp: Annotated[int,
                         Query(description=TIMESTAMP_DESCRIPTION)]
    metadata: Annotated[Dict[str, object] | None,
                        Query(description=METADATA_DESCRIPTION)] = None
