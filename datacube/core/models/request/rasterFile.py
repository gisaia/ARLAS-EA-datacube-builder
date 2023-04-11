from pydantic import BaseModel, Field

from datacube.core.models.request.rasterProductType import RasterType

TYPE_DESCRIPTION = "The type of the raster file."
PATH_DESCRIPTION = "The path to the raster file."
ID_DESCRIPTION = "Identifier for the raster file, " + \
    "used for the traceability of the datacube."


class RasterFile(BaseModel):
    type: RasterType = Field(description=TYPE_DESCRIPTION)
    path: str = Field(description=PATH_DESCRIPTION)
    id: str = Field(description=ID_DESCRIPTION)
