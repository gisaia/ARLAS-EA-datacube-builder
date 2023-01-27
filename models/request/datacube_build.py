from flask_restx import Model, fields
from typing import Dict

from .rasterProductType import RasterProductType
from .rasterGroup import RASTERGROUP_MODEL, RasterGroup
from .band import BAND_MODEL, Band

from models.errors import BadRequest

from utils.enums import RGB, ChunkingStrategy as CStrat
from utils.geometry import roi2geometry

DATACUBE_BUILD_REQUEST = Model(
    "DatacubeBuildRequest",
    {
        "composition": fields.List(
            fields.Nested(RASTERGROUP_MODEL),
            required=True,
            readonly=True
        ),
        "dataCubePath": fields.String(
            required=True,
            readonly=True,
            description="The Object Store path to the datacube."
        ),
        "roi": fields.String(
            required=True,
            readonly=True,
            description="The Region Of Interest to extract. " +
                        "Accepted formats are BBOX or WKT POLYGON."
        ),
        "bands": fields.List(
            fields.Nested(BAND_MODEL),
            required=True,
            readonly=True,
            description="The list of bands to extract."
        ),
        "aliases": fields.Raw(
            required=True,
            readonly=True,
            description="The dictionnary of aliases for this datacube." +
                        "Expected format (key:value) alias:(source, format)."
        ),
        "targetResolution": fields.Integer(
            readonly=True,
            description="The requested spatial resolution in meters."
        ),
        "targetProjection": fields.String(
            readonly=True,
            description="The targeted projection. Default: 'EPSG:4326'."
        ),
        "chunkingStrategy": fields.String(
            readonly=True,
            description="Defines how we want the datacube to be chunked, " +
                        "to facilitate further data processing. Three " +
                        "strategies are available: 'carrot', 'potato' and " +
                        "'spinach'. 'Carrot' creates deep temporal slices, " +
                        "while 'spinach' chunks data on wide geographical " +
                        "areas. 'Potato' is a balanced option, creating " +
                        "an equally sized chunk.",
            enum=["carrot", "potato", "spinach"]
        )
    }
)


class DatacubeBuildRequest:

    def __init__(self, composition, dataCubePath, bands, aliases: Dict,
                 roi=None, targetResolution=None, targetProjection=None,
                 chunkingStrategy=None):
        self.composition = [
            RasterGroup(**rasterGroup) for rasterGroup in composition]
        self.dataCubePath: str = dataCubePath
        self.bands = [Band(**band) for band in bands]

        # Check if aliases were given for every type of product requested
        if type(aliases) is not dict:
            raise BadRequest("Aliases must be a dictionnary")
        self.aliases = {alias: RasterProductType(*_type)
                        for alias, _type in aliases.items()}

        for group in self.composition:
            for file in group.rasters:
                if file.type not in self.aliases.values():
                    raise BadRequest("Aliases were not defined for type: " +
                                     f"source:{file.type.source}, " +
                                     f"format:{file.type.format}")

        self.roi = roi2geometry(roi)

        self.targetResolution = targetResolution \
            if targetResolution is not None \
            else 10
        self.targetProjection = targetProjection \
            if targetProjection is not None \
            else "EPSG:4326"
        self.chunkingStrategy = CStrat(chunkingStrategy) \
            if chunkingStrategy is not None \
            else CStrat.POTATO

        # Check that RGB has been fully filled or not filled
        self.rgb: Dict[RGB, str] = {}
        for band in self.bands:
            if band.rgb is not None:
                if band.rgb in self.rgb:
                    raise BadRequest(
                        f"Too many bands given for color {band.rgb.value}")
                self.rgb[band.rgb] = band.name
            # If no value is given,
            # then the band name needs to include an alias
            if band.value is None:
                if len(band.name.split(".", 1)) == 1:
                    raise BadRequest(f"Band '{band.name}' needs to indicate " +
                                     "the type of product it is linked to, " +
                                     f"by writing it as 'alias.{band.name}'." +
                                     " 'alias' is an alias to a product type.")

        if self.rgb != {} and len(self.rgb.keys()) != 3:
            raise BadRequest("The request should contain no bands with " +
                             "a non null 'rgb' value or 'RED', 'GREEN' " +
                             "and 'BLUE' should be assigned.")

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        request = {}
        request["composition"] = self.composition
        request["dataCubePath"] = self.dataCubePath
        request["roi"] = self.roi
        request["bands"] = self.bands
        request["rgb"] = self.rgb
        request["targetResolution"] = self.targetResolution
        request["targetProjection"] = self.targetProjection
        request["chunkingStrategy"] = self.chunkingStrategy
        request["aliases"] = {alias: _type.as_dict()
                              for alias, _type in self.aliases.items()}

        return str(request)
