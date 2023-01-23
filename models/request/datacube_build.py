from flask_restx import Model, fields
import re
import numpy as np
from typing import Dict

from .rasterGroup import RASTERGROUP_MODEL, RasterGroup
from .asset import ASSET_MODEL, Asset

from utils.enums import RGB, ChunkingStrategy as CStrat
from utils.geometry import roi2geometry

DATACUBE_BUILD_REQUEST = Model(
    "DatacubeBuildRequest",
    {
        "composition": fields.List(
            fields.Nested(RASTERGROUP_MODEL),
            required=True,
            readonly=True),
        "dataCubePath": fields.String(
            required=True,
            readonly=True,
            description="The Object Store path to the data cube"),
        "roi": fields.String(
            required=True,
            readonly=True,
            description="The Region Of Interest to extract. " +
                        "Accepted formats are BBOX or WKT POLYGON"),
        "assets": fields.List(
            fields.Nested(ASSET_MODEL),
            readonly=True,
            description="The list of bands to extract"),
        "targetResolution": fields.Integer(
            readonly=True,
            description="The requested spatial resolution in meters"
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

    def __init__(self, composition, dataCubePath, assets,
                 roi=None, targetResolution=None, targetProjection=None,
                 chunkingStrategy=None):
        self.composition = [
            RasterGroup(**rasterGroup) for rasterGroup in composition]
        self.dataCubePath = dataCubePath
        self.assets = [Asset(**asset) for asset in assets]
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

        # Extract from the request which bands are required
        bands = []
        for asset in self.assets:
            # If no value we take the band name
            if asset.value is None:
                bands.append(asset.name)
            # If a value is given we need to extract the bands required
            # from the expression
            else:
                match = re.findall(r'datacube\.((?!get|where\b)\w*)',
                                   asset.value)
                bands.extend(match)
                match = re.findall(r'datacube\[[\'|\"](\w*)[\'|\"]\]',
                                   asset.value)
                bands.extend(match)
                match = re.findall(r'datacube\.get\([\'|\"](\w*)[\'|\"]\)',
                                   asset.value)
                bands.extend(match)
        self.bands = np.unique(bands)

        # Check that RGB has been fully filled or not filled
        self.rgb: Dict[RGB, str] = {}
        for asset in self.assets:
            if asset.rgb is not None:
                if asset.rgb in self.rgb:
                    raise ValueError(
                        f"Too many assets given for color {asset.rgb.value}")
                self.rgb[asset.rgb] = asset.name

        if self.rgb != {} and len(self.rgb.keys()) != 3:
            raise ValueError("The request should contain no assets with " +
                             "a non null 'rgb' value or 'RED', 'GREEN' " +
                             "and 'BLUE' should be assigned.")

    def __repr__(self):
        request = {}
        request["composition"] = self.composition
        request["dataCubePath"] = self.dataCubePath
        request["roi"] = self.roi
        request["assets"] = self.assets
        request["bands"] = self.bands
        request["rgb"] = self.rgb
        request["targetResolution"] = self.targetResolution
        request["targetProjection"] = self.targetProjection
        request["chunkingStrategy"] = self.chunkingStrategy

        return str(request)
