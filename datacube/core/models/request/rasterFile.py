from pydantic import BaseModel, Field

from datacube.core.models.request.rasterProductType import RasterType

TYPE_DESCRIPTION = "Designates the type of raster file this one is, " + \
                   "to process it with the correct driver."
PATH_DESCRIPTION = "The storage path to the raster file."
ID_DESCRIPTION = "Unique identifier for the raster file " + \
    "used for the traceability of the datacube."


class RasterFile(BaseModel):
    type: RasterType = Field(description=TYPE_DESCRIPTION)
    path: str = Field(description=PATH_DESCRIPTION)
    id: str = Field(description=ID_DESCRIPTION)
