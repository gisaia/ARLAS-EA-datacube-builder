from flask_restx import Model, fields
from dataclasses import dataclass

DATACUBE_BUILD_RESPONSE = Model(
    "DatacubeBuildResponse",
    {
        "datacubeURL": fields.String(
            description="The URL at which the datacube is created"),
        "previewURL": fields.String(
            description="The URL at which the datacube's preview is created"),
        "preview": fields.String(
            description="The preview of the datacube encoded in base64")
    }
)


@dataclass
class DatacubeBuildResponse:
    datacubeURL: str
    previewURL: str
    preview: str
