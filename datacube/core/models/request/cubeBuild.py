from typing import Dict, List, Annotated
from fastapi import Query
from pydantic import BaseModel
from shapely.geometry import Polygon

from datacube.core.models.request.rasterProductType import RasterProductType
from datacube.core.models.request.rasterGroup import RasterGroup
from datacube.core.models.request.band import Band
from datacube.core.models.errors import BadRequest
from datacube.core.models.enums import RGB, ChunkingStrategy as CStrat
from datacube.core.geo.utils import roi2geometry

COMPOSITION_DESCRIPTION = ""
DATACUBEPATH_DESCRIPTION = "The Object Store path to the datacube."
BANDS_DESCRIPTION = "The list of bands to extract."
ALIASES_DESCRIPTION = "The dictionnary of aliases for this datacube." + \
                        "Expected format (key:value) alias:(source, format)."
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
    composition: Annotated[
        List[RasterGroup], Query(description=COMPOSITION_DESCRIPTION)]
    datacube_path: Annotated[
        str, Query(description=DATACUBEPATH_DESCRIPTION)]
    bands: Annotated[
        List[Band], Query(description=BANDS_DESCRIPTION)]
    aliases: Annotated[
        Dict[str, List[str]], Query(description=ALIASES_DESCRIPTION)]
    roi: Annotated[
        str, Query(description=ROI_DESCRIPTION)]
    target_resolution: Annotated[
        int, Query(description=RESOLUTION_DESCRIPTION, gt=0)] = 10
    target_projection: Annotated[
        str, Query(description=PROJECTION_DESCRIPTION)] = "EPSG:4326"
    chunking_strategy: Annotated[
        CStrat, Query(description=CHUNKING_DESCRIPTION)] = CStrat.POTATO


class ExtendedCubeBuildRequest(CubeBuildRequest, arbitrary_types_allowed=True):
    roi_polygon: Annotated[
        Polygon, None] = Polygon()
    product_aliases: Annotated[
        Dict[str, RasterProductType], None] = {}
    rgb: Annotated[
        Dict[RGB, str], None] = {}

    def __init__(self, request: CubeBuildRequest):
        super().__init__(**request.dict())

        self.roi_polygon = roi2geometry(request.roi)

        for k, v in request.aliases.items():
            if len(v) != 2:
                raise BadRequest("Aliases should be specified" +
                                 "with source and format as values")
            self.product_aliases[k] = RasterProductType(
                source=v[0], format=v[1])
        for group in self.composition:
            for file in group.rasters:
                if file.type not in self.product_aliases.values():
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

        if self.rgb != {} and len(self.rgb.keys()) != 3:
            raise BadRequest("The request should contain no bands with " +
                             "a non null 'rgb' value or 'RED', 'GREEN' " +
                             "and 'BLUE' should be assigned.")
