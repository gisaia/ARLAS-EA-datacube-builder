from flask_restx import Model, fields

from .rasterFile import RASTERFILE_MODEL

DATACUBE_BUILD_REQUEST = Model(
    "DatacubeBuildRequest",
    {
        "rasterCompositions": fields.List(
            fields.Nested(RASTERFILE_MODEL),
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
            description="The targeted projection. Default :'EPSG:4326'."
        )
    }
)
