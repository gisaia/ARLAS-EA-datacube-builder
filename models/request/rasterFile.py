from flask_restx import Model, fields

RASTERFILE_MODEL = Model(
    "RasterFile",
    {
        "format": fields.String(
            required=True,
            readonly=True,
            description="The format of the raster file.",
            enum=["2A-Theia", "2A"]
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
        )
    }
)
