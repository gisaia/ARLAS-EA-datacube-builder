from flask_restx import Model, fields

from .rasterGroup import RASTERGROUP_MODEL, RasterGroup

from utils.geometry import bbox2polygon

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
            description="The Region Of Interest (bbox) to extract"),
        "bands": fields.List(
            fields.String,
            readonly=True,
            description="The list of bands to extract"),
        "targetResolution": fields.Integer(
            readonly=True,
            description="The requested end resolution in meters"
        ),
        "targetProjection": fields.String(
            readonly=True,
            description="The targeted projection. Default: 'EPSG:4326'."
        )
    }
)


class DatacubeBuildRequest:

    def __init__(self, composition, dataCubePath, bands,
                 roi=None, targetResolution=None, targetProjection=None):
        self.composition = [
            RasterGroup(**rasterGroup) for rasterGroup in composition]
        self.dataCubePath = dataCubePath
        self.bands = bands

        self.roi = bbox2polygon(roi) \
            if roi is not None \
            else None
        self.targetResolution = targetResolution \
            if targetResolution is not None \
            else 10
        self.targetProjection = targetProjection \
            if targetProjection is not None \
            else "EPSG:4326"

    def __repr__(self):
        request = {}
        request["composition"] = self.composition
        request["dataCubePath"] = self.dataCubePath
        request["roi"] = self.roi
        request["bands"] = self.bands
        request["targetResolution"] = self.targetResolution
        request["targetProjection"] = self.targetProjection

        return str(request)
