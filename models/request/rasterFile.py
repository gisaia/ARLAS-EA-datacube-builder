from flask_restx import Model, fields

RASTERFILE_MODEL = Model(
    "RasterFile",
    {
        "format": fields.String(
            required=True,
            readonly=True,
            description="The format of the raster file.",
            enum=["2A-Theia", "2A-Safe"]
        ),
        "source": fields.String(
            required=True,
            readonly=True,
            description="The source of the raster file.",
            enum=["Sentinel2"]
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

    def __init__(self, format, source, path, id):
        self.format = format
        self.source = source
        self.path = path
        self.id = id

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        rasterFile = {}
        rasterFile["format"] = self.format
        rasterFile["source"] = self.source
        rasterFile["path"] = self.path
        rasterFile["id"] = self.id

        return rasterFile
