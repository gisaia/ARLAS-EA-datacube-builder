from pydantic import BaseModel, Field
from shapely.geometry import Polygon

from datacube.core.geo.utils import roi2geometry
from datacube.core.models.enums import RGB
from datacube.core.models.enums import ChunkingStrategy as CStrat
from datacube.core.models.errors import BadRequest
from datacube.core.models.request.band import Band
from datacube.core.models.request.rasterGroup import RasterGroup
from datacube.core.models.request.rasterProductType import (AliasedRasterType,
                                                            RasterType)

COMPOSITION_DESCRIPTION = "The composition is an array of raster groups " + \
                          "that each represent a temporal slice of " + \
                          "the datacube. The whole composition contains " + \
                          "all the data requested across space and time."
DATACUBEPATH_DESCRIPTION = "The path to the datacube. " + \
                           "Can be in the local storage or in an object store."
BANDS_DESCRIPTION = "The list of bands to extract. " + \
                    "The bands will be the variables of the datacube/zarr."
ALIASES_DESCRIPTION = "The list of aliases for this datacube. " + \
                      "They will allow to quickly reference the " + \
                      "product bands used to compute the datacube bands."
ROI_DESCRIPTION = "The Region Of Interest to extract. " + \
                  "Accepted formats are BBOX or WKT POLYGON."
RESOLUTION_DESCRIPTION = "The requested spatial resolution in meters."
PROJECTION_DESCRIPTION = "The targeted projection. Default: 'EPSG:4326'."
CHUNKING_DESCRIPTION = "Defines how we want the datacube to be chunked, " + \
                       "to facilitate further data processing. Three " + \
                       "strategies are available: 'carrot', 'potato' and " + \
                       "'spinach'. 'Carrot' creates deep temporal slices, " + \
                       "while 'spinach' chunks data on wide geographical " + \
                       "areas. 'Potato' is a balanced option, creating " + \
                       "an equally sized chunk."


class CubeBuildRequest(BaseModel):
    composition: list[RasterGroup] = Field(description=COMPOSITION_DESCRIPTION)
    datacube_path: str = Field(description=DATACUBEPATH_DESCRIPTION)
    bands: list[Band] = Field(description=BANDS_DESCRIPTION)
    aliases: list[AliasedRasterType] = Field(description=ALIASES_DESCRIPTION)
    roi: str = Field(description=ROI_DESCRIPTION)
    target_resolution: int = Field(default=10,
                                   description=RESOLUTION_DESCRIPTION, gt=0)
    target_projection: str = Field(default="EPSG:4326",
                                   description=PROJECTION_DESCRIPTION)
    chunking_strategy: CStrat = Field(default=CStrat.POTATO,
                                      description=CHUNKING_DESCRIPTION)


class ExtendedCubeBuildRequest(CubeBuildRequest, arbitrary_types_allowed=True):
    roi_polygon: Polygon = Field(default=Polygon())
    rgb: dict[RGB, str] = Field(default={})

    def __init__(self, request: CubeBuildRequest):
        super().__init__(**request.dict())

        self.roi_polygon = roi2geometry(request.roi)

        aliased_types = list(map(lambda a: RasterType(**a.dict()),
                                 self.aliases))
        for group in self.composition:
            for file in group.rasters:
                if file.type not in aliased_types:
                    raise BadRequest("Aliases were not defined for type: " +
                                     f"source:{file.type.source}, " +
                                     f"format:{file.type.format}")

        for band in self.bands:
            band.check_visualistion()
            if band.rgb is not None:
                if band.rgb in self.rgb:
                    raise BadRequest(
                        f"Too many bands given for color {band.rgb.value}")
                self.rgb[band.rgb] = band.name

        if len(self.rgb) != 3 and len(self.rgb) != 0:
            raise BadRequest("The request should either contain no bands " +
                             "with a set 'rgb' value or 'RED', 'GREEN' " +
                             "and 'BLUE' should be assigned to " +
                             "the bands of the datacube.")
