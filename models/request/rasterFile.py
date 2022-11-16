from flask_restx import Model, fields


RASTERFILE_MODEL = Model(
    "RasterComposition",
    {
        "rasterFormat": fields.String(
            required=True,
            readonly=True,
            description="The origin of the raster file.",
            enum=["Sentinel2-2A"]
        ),
        "rasterPath": fields.String(
            required=True,
            readonly=True,
            description="The path to the raster file."
        ),
        "rasterTimestamp": fields.Integer(
            required=True,
            readonly=True,
            description="The timestamp of the raster's temporal bucket."
        )
    }
)
