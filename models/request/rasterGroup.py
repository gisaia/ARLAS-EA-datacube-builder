from flask_restx import Model, fields

from .rasterFile import RASTERFILE_MODEL
from utils.flaskFields import DictItem

RASTERGROUP_MODEL = Model(
    "RasterGroup",
    {
        "rasters": fields.List(
            fields.Nested(RASTERFILE_MODEL),
            required=True,
            readonly=True,
            description="The list of raster files in this group."
        ),
        "timestamp": fields.Integer(
            required=True,
            readonly=True,
            description="The timestamp of this temporal group."
        ),
        "metadata": DictItem(
            required=False,
            readonly=True,
            description="Optional metadata for this group."
        )
    }
)
