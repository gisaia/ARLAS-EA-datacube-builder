from flask_restx import Model, fields
import re
import numpy as np

from .rasterGroup import RASTERGROUP_MODEL, RasterGroup
from .asset import ASSET_MODEL, Asset

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
        )
    }
)


class DatacubeBuildRequest:

    def __init__(self, composition, dataCubePath, assets,
                 roi=None, targetResolution=None, targetProjection=None):
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

    def __repr__(self):
        request = {}
        request["composition"] = self.composition
        request["dataCubePath"] = self.dataCubePath
        request["roi"] = self.roi
        request["assets"] = self.assets
        request["bands"] = self.bands
        request["targetResolution"] = self.targetResolution
        request["targetProjection"] = self.targetProjection

        return str(request)
