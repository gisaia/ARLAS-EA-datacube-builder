from flask_restx import Model, fields

from .rasterProductType import RASTERPRODUCTTYPE_MODEL, RasterProductType

RASTERFILE_MODEL = Model(
    "RasterFile",
    {
        "type": fields.Nested(
            RASTERPRODUCTTYPE_MODEL,
            required=True,
            readonly=True
        ),
        "path": fields.String(
            required=True,
            readonly=True,
            description="The path to the raster file."
        ),
        "id": fields.String(
            required=True,
            readonly=True,
            description="Identifier for the raster file," +
                        "used for the traceability of the datacube."
        )
    }
)


class RasterFile:

    def __init__(self, type, path, id):
        self.type = RasterProductType(**type)
        self.path: str = path
        self.id: str = id

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        rasterFile = {}
        rasterFile["type"] = self.type.as_dict()
        rasterFile["path"] = self.path
        rasterFile["id"] = self.id

        return rasterFile
