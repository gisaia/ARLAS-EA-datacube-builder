from pydantic import BaseModel, Field

from datacube.core.models.request.rasterFile import RasterFile

RASTERS_DESCRIPTION = "The list of raster files in this group."
TIMESTAMP_DESCRIPTION = "The timestamp of this group."


class RasterGroup(BaseModel):
    rasters: list[RasterFile] = Field(description=RASTERS_DESCRIPTION)
    timestamp: int = Field(description=TIMESTAMP_DESCRIPTION)
