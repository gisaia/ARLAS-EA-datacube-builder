from pydantic import BaseModel, Field

from datacube.core.models.request.rasterFile import RasterFile

RASTERS_DESCRIPTION = "The list of raster files in this group. " + \
                      "They represent a temporal slice of the datacube."
TIMESTAMP_DESCRIPTION = "The timestamp of this temporal slice of the datacube."


class RasterGroup(BaseModel):
    rasters: list[RasterFile] = Field(description=RASTERS_DESCRIPTION)
    timestamp: int = Field(description=TIMESTAMP_DESCRIPTION)
