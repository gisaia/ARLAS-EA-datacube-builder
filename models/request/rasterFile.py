from flask_restx import Model, fields


RASTERFILE_MODEL = Model(
    "RasterFile",
    {
        "rasterFormat": fields.String(
            required=True,
            readonly=True,
            description="The format of the raster file. For example 'Sentinel2-2A'."
        ),
        "rasterPath": fields.String(
            required=True,
            readonly=True,
            description="The path to the raster file."
        )
    }
)
